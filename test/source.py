import unittest
import sys
import os
import commands
import re

from bake.ModuleEnvironment import ModuleEnvironment
from bake.ModuleLogger import StdoutModuleLogger
from bake.Exceptions import TaskError

from bake.ModuleSource import ModuleSource

class TestModuleSource(unittest.TestCase):
    """Tests cases for the Module Environment Class."""
    
    def setUp(self):
        """Common set Up environment, available for all tests."""
        pathname = os.path.dirname("/tmp/")  
        self._logger = StdoutModuleLogger();
        self._logger.set_verbose(1)
        self._env = ModuleEnvironment(self._logger, pathname, pathname, pathname)
       
    def tearDown(self):
        """Cleans the environment environment for the next tests."""
        self._env = None 

    def executeCommand(self, command, dir):
        """Executes the given command, catching the exceptions."""
        
        try:
            self._env.run(command, dir)
        except Exception as inst:
            print (inst)     # the exception instance
            self.fail("Could not execute command %s over directory %s failed" % (command, dir))

    def Disable_test_generalFailures(self):
        """Tests Some general failures that could happen in the Module Source. """
        
        #Verifies the return of the creation of a non existent module
        module = ModuleSource.create("NonExistentModule")
        self.assertEqual(module, None)

    def test_archiveModuleSource(self):
        """Tests the ArchiveModuleSource class. """
        
        # it first needs to be able to create the class otherwise will not be
        # able to do anything else
        archive = ModuleSource.create("archive")
        self.assertNotEqual(archive, None)
        self.assertEqual(archive.name(), "archive")
        
        # Verifies if the system has the right tools installed, if not does not
        # even worth continuing
        
        # no file was declared yet, so the issue should be False
        testResult = archive.check_version(self._env)
        self.assertFalse(testResult)    
       
        # Unknown file type
        archive.attribute("url").value = "http://JustATest.com/File.unknownFileType"
        testResult = archive.check_version(self._env)
        self.assertFalse(testResult, "There is no tool to handle the target extension, the result should be false")    
        # zip
        archive.attribute("url").value = "http://JustATest.com/File.zip"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "unzip is not present on the system")    
        # rar
        archive.attribute("url").value = "http://JustATest.com/File.rar"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "unrar is not present on the system")    
        # tar
        archive.attribute("url").value = "http://JustATest.com/File.tar"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.Z
        archive.attribute("url").value = "http://JustATest.com/File.tar.Z"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.bz2
        archive.attribute("url").value = "http://JustATest.com/File.tar.bz2"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
        # tar.gz
        archive.attribute("url").value = "http://read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        testResult = archive.check_version(self._env)
        self.assertTrue(testResult, "tar is not present on the system")    
      
        
        self._env._module_name="click-1.8.0"
        self._logger.set_current_module(self._env._module_name)
        
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0.tar.gz"], "/tmp")
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0"], "/tmp")
        testResult = archive.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)
        
        # verifies that files are really there after the download
        testStatus = commands.getoutput('ls /tmp/click-1.8.0.tar.gz')
        self.assertEqual("/tmp/click-1.8.0.tar.gz", testStatus)
 
        testStatus = commands.getoutput('ls -d /tmp/click-1.8.0')
        self.assertEqual("/tmp/click-1.8.0", testStatus)
      
        #after the test, clean the environment
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0.tar.gz"], "/tmp")
        self.executeCommand(["/bin/rm", "-rf", "click-1.8.0"], "/tmp")

        # Searches for a valid file into an inexistent repository
        archive.attribute("url").value = "http://non.existent.host.com/click-1.8.0.tar.gz"
        testResult = None
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, and the server does not exist. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # Try to download to a directory that the user has no permission
        archive.attribute("url").value = "http://read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        testStatus = commands.getoutput('touch /tmp/click-1.8.0;chmod 000 /tmp/click-1.8.0')    
        testResult = None
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, the user has no permission over the target directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/click-1.8.0; rm -f /tmp/click-1.8.0')

        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = None
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        testResult = None
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # no protocol download url gives you an error
        archive.attribute("url").value = "read.cs.ucla.edu/click/click-1.8.0.tar.gz"
        testResult = None
        try:
            testResult = archive.download(self._env)
            self.fail("There was no problem, the user didn't add the protocol for the url. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # just to be sure that the update does nothing
        testResult = archive.update(self._env)
        self.assertEqual(testResult, None)

        # Oddly enough, when the user has no permission in the target 
        # directory the system returns no error Right now I have no idea how
        # to fix it, or IF we should try to fix anyway.
#        self._env._sourcedir = "/tmp"
#        testStatus = commands.getoutput('mkdir /tmp/click-1.8.0;chmod 000 /tmp/click-1.8.0')       
#        try:
#            testResult = archive.download(self._env)
#            self.fail("There was not problem, the user has no permission over the target directory. ")
#        except TaskError as e:
#            self.assertNotEqual(e._reason, None)    
#            self.assertEqual(testResult, None)
#
#        testStatus = commands.getoutput('chmod 755 /tmp/click-1.8.0; rm -rf /tmp/click-1.8.0')


    def Disable_test_mercurial(self):
        """Tests the MercurialModuleSource class. """
        
        # it first needs to be able to create the class otherwise will not be
        # able to do anything else
        mercurial = ModuleSource.create("mercurial")
        self.assertNotEqual(mercurial, None)
        self.assertEqual(mercurial.name(), "mercurial")
       
        # Verifies if the system has the mercurial installed, if not does not
        # even worth continuing
        testResult = mercurial.check_version(self._env)
        self.assertTrue(testResult)

        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._logger.set_current_module(self._env._module_name)
        
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "bake"], "/tmp")
        testResult = mercurial.download(self._env)
        
        # if something goes wrong it should rise an exception so, None means 
        # everything is OK
        self.assertEqual(testResult, None)
        
        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
       
        # download a specific version
        mercurial.attribute("revision").value = "63"
        testResult = mercurial.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "63")

        # makes an update of the version to the last version
        mercurial.attribute("revision").value = "64"
        testResult = mercurial.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "64")
        
        # Verifies the update to the tip
        mercurial.attribute("revision").value = "tip"
        testResult = mercurial.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/bake;hg log')
        versionRepository = re.compile('\d+').search(testStatus).group()
        testStatus = commands.getoutput('cd /tmp/bake;hg summary')
        versionDownloaded = re.compile('\d+').search(testStatus).group()
        self.assertEqual(versionRepository, versionDownloaded)
        
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
          
        # Not http should give you a TaskError exception
        mercurial.attribute("url").value = "code.nsnam.org/daniel/bake"
        self._env._module_name="bake"
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
        testStatus = commands.getoutput('mkdir /tmp/bake;chmod 000 /tmp/bake')    
        mercurial.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        testResult = None
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem and the user has no permission over the directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('chmod 755 /tmp/bake')    
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")
        
        # try to download to a non existent directory
        # mercurial cretes the directory
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = mercurial.download(self._env)
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
          
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        testResult = None
        try:
            testResult = mercurial.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')

 
        # Try to get a wrong version, there is a but in the mercurial
        # that permits negative revisions, such as -34, for example, 
        # however bigger than the tip version gives an error
        mercurial.attribute("revision").value = "9999999"
        testResult = None
        try:
            testResult = mercurial.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # last clean up
        self.executeCommand(["rm", "-rf", "bake"], "/tmp")

    def Disable_test_bazaar(self):
        """Tests the BazaarModuleSource class. """
        
        # checks if can create the class 
        bazaar = ModuleSource.create("bazaar")
        self.assertNotEqual(bazaar, None)
        self.assertEqual(bazaar.name(), "bazaar")
       
        # Verifies if Bazaar is installed
        testResult = bazaar.check_version(self._env)
        self.assertTrue(testResult)

        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        self._env._module_name="pybindgen"
        self._logger.set_current_module(self._env._module_name)
        
        ##### Normal Flow test
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "pybindgen"], "/tmp")
        testResult = bazaar.download(self._env)
        
        # None means everything was OK, since there were no exceptions
        self.assertEqual(testResult, None)
        
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        lastVersion = re.compile('\d+').search(testStatus).group()

        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
       
        # download a specific version
        bazaar.attribute("revision").value = "794"
        testResult = bazaar.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "794")

        # makes an update of the version to a latter version
        bazaar.attribute("revision").value = "795"
        testResult = bazaar.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/pybindgen; bzr log')
        version = re.compile('\d+').search(testStatus).group()
        self.assertEqual(version, "795")
        
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
          
        # Wrong repository
        bazaar.attribute("url").value = "http://code.nsnam.org/daniel/bake"
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
 
        # No protocol http/https
        bazaar.attribute("url").value = "launchpad.net/pybindgen"
        bazaar.attribute("revision").value = None
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem not passing the protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
        
        testStatus = commands.getoutput('mkdir /tmp/pybindgen;chmod 000 /tmp/pybindgen')    
        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem and the user has no permission over the directory. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
            
        testStatus = commands.getoutput('chmod 755 /tmp/pybindgen')    
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")
        
        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # try to download to a directory where the user has no permission    
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # returns to the original state
        bazaar.attribute("url").value = "https://launchpad.net/pybindgen"
        self._env._sourcedir = "/tmp"

        # Try to get an unavailable version
        bazaar.attribute("revision").value = str(int(lastVersion) + 1)
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # verifies the update to a inexistent version
        bazaar.attribute("revision").value = None
        testResult = bazaar.download(self._env)
        self.assertEqual(testResult, None)
                    
        # Invalid argument, it is int and should be string
        bazaar.attribute("revision").value = -60
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # can not go for a negative version
        bazaar.attribute("revision").value = str(-60)
        testResult = None
        try:
            testResult = bazaar.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
  
        # last clean up
        self.executeCommand(["rm", "-rf", "pybindgen"], "/tmp")

    def test_cvs(self):
        """Tests the CvsModuleSourceclass. """
        
        # checks if can create the class 
        cvs = ModuleSource.create("cvs")
        self.assertNotEqual(cvs, None)
        self.assertEqual(cvs.name(), "cvs")
       
        # Verifies if cvs is installed
        testResult = cvs.check_version(self._env)
        self.assertTrue(testResult)

        cvs.attribute("root").value = ":pserver:anoncvs:@www.gccxml.org:/cvsroot/GCC_XML"
        cvs.attribute("module").value="gccxml"
        cvs.attribute("date").value="2009-09-21"
        
        self._env._module_name="gccxml"
        self._logger.set_current_module(self._env._module_name)

        ##### Normal Flow test
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "gccxml"], "/tmp")
        testResult = cvs.download(self._env)

        # None means everything was OK, since there were no exceptions
        self.assertEqual(testResult, None)
        
        # will use the README file to see if the update works
        testStatus = commands.getoutput('cd /tmp/gccxml; cvs status CMakeLists.txt')
        lastVersion = re.compile('\d+.\d+').search(testStatus).group().replace(".","")

        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")
        
      
        # download a specific version
        cvs.attribute("date").value="2007-09-21"
        testResult = cvs.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/gccxml; cvs status CMakeLists.txt')
        version = re.compile('\d+.\d+').search(testStatus).group().replace(".","")
        self.assertEqual(version, "18")

        # makes an update of the version to a latter version
        cvs.attribute("date").value="2008-09-21"
        testResult = cvs.update(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is bigger than the previous one
        testStatus = commands.getoutput('cd /tmp/gccxml; cvs status CMakeLists.txt')
        version2 = re.compile('\d+.\d+').search(testStatus).group().replace(".","")
        self.assertTrue((float(version) < float(version2)))
        
        # Verify if it updates to today's version
        cvs.attribute("date").value=None
        testResult = cvs.update(self._env)       
        self.assertEqual(testResult, None)
        testStatus = commands.getoutput('cd /tmp/gccxml; cvs status CMakeLists.txt')
        version3 = re.compile('\d+.\d+').search(testStatus).group().replace(".","")
        self.assertTrue(float(version2) < float(version3))

        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")
          
        # Wrong repository
        cvs.attribute("root").value = ":pserver:anoncvs:@non.Existent.server.com:/cvsroot/GCC_XML"
        cvs.attribute("date").value="2008-09-21"
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = cvs.download(self._env)
            self.fail("There was no problem with a non existent repository. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
             
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")

        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = None
        try:
            testResult = cvs.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # try to download to a directory where the user has no permission    
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        testResult = None
        try:
            testResult = cvs.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # returns to the original state
        cvs.attribute("root").value = ":pserver:anoncvs:@www.gccxml.org:/cvsroot/GCC_XML"
        self._env._sourcedir = "/tmp"
               
        # Invalid argument, it is int and should be string
        cvs.attribute("checkout_directory").value = -60
        testResult = None
        try:
            testResult = cvs.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # can't go for an inexistent version 
        cvs.attribute("checkout_directory").value = "/tmp"
        cvs.attribute("date").value="5000-09-21"
        testResult = None
        try:
            testResult = cvs.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # last clean up
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")
        
    def Disable_test_git(self):
        """Tests the GitModuleSource. """
        
        # checks if can create the class 
        git = ModuleSource.create("git")
        self.assertNotEqual(git, None)
        self.assertEqual(git.name(), "git")
       
        # Verifies if git is installed
        testResult = git.check_version(self._env)
        self.assertTrue(testResult)

        git.attribute("url").value = "git://github.com/git/hello-world.git"
        git.attribute("revision").value = "78cfc43c2827b9e48e6586a3523ff845a6378889"
        
        self._env._module_name="hello-world"
        self._logger.set_current_module(self._env._module_name)
        
        ##### Normal Flow test
        #clean up the environment, just to be safe
        self.executeCommand(["/bin/rm", "-rf", "hello-world"], "/tmp")
        testResult = git.download(self._env)

        # None means everything was OK, since there were no exceptions
        self.assertEqual(testResult, None)
        
        # will use the README file to see if the update works
        testStatus = commands.getoutput('cd /tmp/hello-world; git log')
        lastVersion = re.compile(' +\w+').search(testStatus).group().replace(" ","")
        self.assertEqual(lastVersion, "78cfc43c2827b9e48e6586a3523ff845a6378889")

        #after the test, clean the environment
        self.executeCommand(["rm", "-rf", "hello-world"], "/tmp")
      
        # download a specific version
        git.attribute("revision").value="3fa7c46d11b11d61f1cbadc6888be5d0eae21969"
        testResult = git.download(self._env)       
        self.assertEqual(testResult, None)
        
        # verify that the version is the correct one
        testStatus = commands.getoutput('cd /tmp/hello-world; git log')
        version = re.compile(' +\w+').search(testStatus).group().replace(" ","")
        self.assertEqual(version, "3fa7c46d11b11d61f1cbadc6888be5d0eae21969")
         
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")
         
        #Wrong repository
        git.attribute("url").value = "git://inexistant.server.com/git/hello-world.git"
        git.attribute("revision").value = "78cfc43c2827b9e48e6586a3523ff845a6378889"
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("There was no problem with a non existent repository. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
             
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")

        # no protocol
        git.attribute("url").value = "github.com/git/hello-world.git"
        self._logger.set_current_module(self._env._module_name)
        
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("There was no problem without protocol. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
             
        git.attribute("url").value = "git://github.com/git/hello-world.git"
        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")

        # try to download to a non existent directory        
        testStatus = commands.getoutput('rm -rf /tmp/testDir')
        self._env._sourcedir = "/tmp/testDir"
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("There was no problem, target directory does not exist and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
        
        # try to download to a directory where the user has no permission    
        testStatus = commands.getoutput('mkdir /tmp/testDir;chmod 000 /tmp/testDir')
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("There was no problem, user has no permission on the target directory and it managed to finish the operation. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        testStatus = commands.getoutput('chmod 755 /tmp/testDir; rm -rf /tmp/testDir')
 
        # Invalid argument, it is int and should be string
        self._env._sourcedir = -60
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)

        # returns to the original state
        self._env._sourcedir = "/tmp"

        # can't go for an inexistent version 
        git.attribute("revision").value = "1000000000000000000000000000000000000000"  
        testResult = None
        try:
            testResult = git.download(self._env)
            self.fail("The version is inexistent, but there is no error. ")
        except TaskError as e:
            self.assertNotEqual(e._reason, None)    
            self.assertEqual(testResult, None)
   
# I guess there is a bug in the move of the os library.... I need to see this
# further later        
#        cvs.attribute("root").value = ":pserver:anoncvs:@www.gccxml.org:/cvsroot/GCC_XML"
#        testStatus = commands.getoutput('mkdir /tmp/gccxml;chmod 000 /tmp/gccxml')    
#        try:
#            testResult = cvs.download(self._env)
#            self.fail("There was no problem and the user has no permission over the directory. ")
#        except TaskError as e:
#            self.assertNotEqual(e._reason, None)    
#            self.assertEqual(testResult, None)
#            
#        testStatus = commands.getoutput('chmod 755 /tmp/gccxml')    
#        self.executeCommand(["rm", "-rf", "gccxml"], "/tmp")


# TODO: 
#    Tests for CvsModuleSource
#              GitModuleSource
#              InlineModuleSource (?!?!?!)

# main call for the tests        
if __name__ == '__main__':
    unittest.main()
