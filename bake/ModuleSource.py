from Exceptions import TaskError
import Utils
from Utils import ModuleAttributeBase
import os
import urlparse
from datetime import date

class ModuleSource(ModuleAttributeBase):
    def __init__(self):
        ModuleAttributeBase.__init__(self)
    @classmethod
    def subclasses(self):
        return ModuleSource.__subclasses__()
    @classmethod
    def create(cls, name):
        """Instantiates the class that is called by the requested name."""
        
        # Runs over all the Classes and instantiates the one that has the name
        # equals to the name passed as parameter
        for subclass in ModuleSource.subclasses():
            if subclass.name() == name:
                return subclass()
        return None
    def diff(self, env):
        raise NotImplemented()
    def download(self, env):
        raise NotImplemented()
    def update(self, env):
        raise NotImplemented()
    def check_version(self, env):
        raise NotImplemented()

class NoneModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'none'
    def diff(self, env):
        pass
    def download(self, env):
        pass
    def update(self, env):
        pass
    def check_version(self, env):
        return True

class InlineModuleSource(ModuleSource):
    def __init__(self):
        ModuleSource.__init__(self)
    @classmethod
    def name(cls):
        return 'inline'

class BazaarModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a bazaar repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                           mandatory = True)
        self.add_attribute('revision', None, 'The revision to update to after the clone.')
    @classmethod
    def name(cls):
        return 'bazaar'
    def diff(self, env):
        pass
    def download(self, env):
        rev_arg = []
        if not self.attribute('revision').value is None:
            rev_arg.extend(['-r', self.attribute('revision').value])
        env.run(['bzr', 'clone'] + rev_arg + [self.attribute('url').value, env.srcdir])

    def update(self, env):
        rev_arg = []
        if not self.attribute('revision').value is None:
            rev_arg.extend(['-r', self.attribute('revision').value])
        env.run(['bzr', 'pull'] + rev_arg + [self.attribute('url').value], directory = env.srcdir)
    def check_version(self, env):
        return env.check_program('bzr')

    
class MercurialModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a mercurial repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'The url to clone from',
                            mandatory = True)
        self.add_attribute('revision', 'tip', 'The revision to update to after the clone. '
                           'If no value is specified, the default is "tip"')
    @classmethod
    def name(cls):
        return 'mercurial'
    def download(self, env):
        env.run(['hg', 'clone', '-U', self.attribute('url').value, env.srcdir])
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory = env.srcdir)
    def update(self, env):
        env.run(['hg', 'pull', self.attribute('url').value], directory = env.srcdir)
        env.run(['hg', 'update', '-r', self.attribute('revision').value],
                directory = env.srcdir)
    def check_version(self, env):
        return env.check_program('hg')

        
class ArchiveModuleSource(ModuleSource):
    """Handles the modules that have the sources as a single tarball like file."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', None, 'The url to clone from',
                           mandatory = True)
        self.add_attribute('extract_directory', None, 
                           'The name of the directory the source code will be extracted to naturally.'
                           ' If no value is specified, directory is assumed to be equal to the '
                           'of the archive without the file extension.')
    @classmethod
    def name(cls):
        return 'archive'
    def _decompress(self, filename, env):
        """Uses the appropriate tool to uncompress the sources."""
        
        import tempfile
        import os
        tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        extensions = [
            ['tar', ['tar', 'xf']],
            ['tar.gz', ['tar', 'zxf']],
            ['tar.Z', ['tar', 'zxf']],
            ['tar.bz2', ['tar', 'jxf']],
            ['zip', ['unzip']],
            ['rar', ['unrar', 'e']]
            ]
        
        # finds the right tool
        for extension, command in extensions:
            if filename.endswith(extension):
                env.run(command + [filename], directory = tempdir)
                if self.attribute('extract_directory').value is not None:
                    actual_extract_dir = self.attribute('extract_directory').value
                else:
                    actual_extract_dir = os.path.basename(filename)[0:-len(extension)-1]
                # finally, rename the extraction directory to the target directory name.
                try:
                    os.rename(os.path.join(tempdir, actual_extract_dir), env.srcdir)
                    os.remove(tempdir)
                except (OSError, IOError) as e:
                    raise TaskError('Rename problem for module: %s, from: %s, to: %s, Error: %s' 
                                    % (env._module_name,os.path.join(tempdir, actual_extract_dir),env.srcdir, e))

                return
        raise TaskError('Unknown Archive Type: %s, for module: %s' %(filename, env._module_name))

    def download(self, env):
        """Downloads the specific file."""
        
        import urllib
        import urlparse
        import os
        filename = os.path.basename(urlparse.urlparse(self.attribute('url').value).path)
        tmpfile = os.path.join(env.srcrepo, filename)
        try:
            urllib.urlretrieve(self.attribute('url').value, filename=tmpfile)
        except IOError as e:
            raise TaskError('Download problem for module: %s, URL: %s, Error: %s' % (env._module_name, self.attribute('url').value, e))
            
        self._decompress(tmpfile, env)
        
    def update(self, env):
        # we really have nothing to do for archives. 
        pass

    def check_version(self, env):
        """Verifies if the right program exists in the system to handle the given compressed source file."""
        
        extensions = [
            ['tar', 'tar'],
            ['tar.gz', 'tar'],
            ['tar.Z', 'tar'],
            ['tar.bz2', 'tar'],
            ['zip', 'unzip'],
            ['rar', 'unrar']
            ]
        try:
            filename = os.path.basename(urlparse.urlparse(self.attribute('url').value).path)
        except AttributeError as e:
            return False

        for extension,program in extensions:
            if filename.endswith(extension):
                return env.check_program(program)
        return False
        
class CvsModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a CVS repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('root', '', 'Repository root specification to checkout from.',
                           mandatory = True)
        self.add_attribute('module', '', 'Module to checkout.', mandatory = True)
        self.add_attribute('checkout_directory', None, 'Name of directory checkout defaults to. '
                           'If unspecified, defaults to the name of the module being checked out.')
        self.add_attribute('date', None, 'Date to checkout')

    @classmethod
    def name(cls):
        return 'cvs'
    def download(self, env):
        """ Downloads the CVS code from a specific date. """
        
        import tempfile
        try:
            tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        except OSError as e:
            raise TaskError('Could not create temporary directory %s, Error: %s' % (env.srcrepo, e))

        env.run(['cvs', '-d', self.attribute('root').value, 'login'], 
                directory = tempdir)
        checkout_options = []
        if not self.attribute('date').value is None:
            checkout_options.extend(['-D', self.attribute('date').value])
        env.run(['cvs', '-d', self.attribute('root').value, 'checkout'] + checkout_options +
                [self.attribute('module').value],
                directory = tempdir)
        if self.attribute('checkout_directory').value is not None:
            actual_checkout_dir = self.attribute('checkout_directory').value
        else:
            actual_checkout_dir = self.attribute('module').value
        import os
        try:
            os.rename(os.path.join(tempdir, actual_checkout_dir), env.srcdir)
            os.remove(tempdir)
        except AttributeError as e:
            raise TaskError('Atribute type error expected String, Error: %s' % e)
        

    def update(self, env):
        """Updates the code for the date specified, or for the today's code. """
        
        # just update does not work, it has to give a date for the update
        # either a date is provided, or takes today as date
        update_options = []
        if not self.attribute('date').value is None:
            update_options.extend(['-D', self.attribute('date').value])
        else:
            update_options.extend(['-D', str(date.today())]) 
        
        env.run(['cvs', 'up']+update_options, directory = env.srcdir)
        
    def check_version(self, env):
        return env.check_program('cvs')

class GitModuleSource(ModuleSource):
    """Handles the modules that have the sources stored in a git repository."""
    
    def __init__(self):
        ModuleSource.__init__(self)
        self.add_attribute('url', '', 'Url to clone the source tree from.',
                           mandatory = True)
        self.add_attribute('revision', 'refs/remotes/origin/master', 
                           'Revision to checkout. Defaults to origin/master reference.')
    @classmethod
    def name(cls):
        return 'git'
    def download(self, env):
        import tempfile
        import os
        try:
            tempdir = tempfile.mkdtemp(dir=env.srcrepo)
        except AttributeError as e1:
            raise TaskError('Atribute type error, expected String, Error: %s' % e1)
        except OSError as e2:
            raise TaskError('Could not create temporary file, Error: %s' % e2)
            
        env.run(['git', 'init'], directory = tempdir)
        env.run(['git', 'remote', 'add', 'origin', self.attribute('url').value], 
                directory = tempdir)
        env.run(['git', 'fetch'], 
                directory = tempdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                directory = tempdir)
        os.rename(tempdir, env.srcdir)

    def update(self, env):
        env.run(['git', 'fetch'], directory = env.srcdir)
        env.run(['git', 'checkout', self.attribute('revision').value],
                          directory = env.srcdir)

    def check_version(self, env):
        return env.check_program('git')
