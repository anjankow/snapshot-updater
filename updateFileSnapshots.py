import re
from typing import List
import os
import getpass
import subprocess


# Finds all test names in a given file
# Warning: test names must conform to the regex:
#   '^func (\w+).*testing.T'
def findTestNames(filePath: str) ->List[str]:
    f = open(filePath, 'r')
    # first let's collect names of the tests
    testNames = []
    for line in f:
        # \w matches word character: (characters from a to Z, digits from 0-9, and the underscore _ character)
        # brackets () capture a group
        testRegex = '^func (\w+).*testing.T'
        matched = re.search(testRegex, line)

        if matched is None:
            continue

        name = matched.group(1)
        testNames.append(name)

    return testNames


# To run all tests from a single file:
#   go test -run ^(TestName1|TestName2)$ package/import/path
#
# goPath: path to go executable
# projectBasePath: absolute directory of the go.mod file
# pkgImportDir: import path of the package owning the file
# filePath: absolute path of the file
def runFileTests(goPath: str, projectBasePath: str, pkgImportDir: str, filePath: str, verbose=True):
    # get test names from the file
    testNames = findTestNames(filePath)
    testNamesStr = ""
    for name in testNames:
        testNamesStr+=name + '|'
    testNamesStr= testNamesStr.removesuffix('|')
    
    # prepare command
    command = [f"{goPath}", "test","-v", "-run", f"^({testNamesStr})$", f"{pkgImportDir}"]
    if not verbose:
         command.remove("-v")

    p = subprocess.Popen(command, cwd=projectBasePath, user=getpass.getuser(), group=os.getgid())
    p.wait()


# to run package tests:
#   go test package/import/path
#
# goPath: path to go executable
# projectBasePath: absolute directory of the go.mod file
# pkgImportDir: import path of the package
def runPackageTests(goPath: str, projectBasePath: str, pkgImportDir: str, verbose=True):
    command = [f"{goPath}", "test","-v", f"{pkgImportDir}"]
    if not verbose:
         command.remove("-v")

    p = subprocess.Popen(command, cwd=projectBasePath, user=getpass.getuser(), group=os.getgid())
    p.wait()


# takes go directory from PATH,
# returns path to the executable
def getGoPath()-> str:
    PATH = os.getenv('PATH')
    matchedIdx = PATH.find('go/bin')
    if matchedIdx < 0:
        print('Error: can\'t find go executable in the PATH')
        return ''

    delimiter = ':'
    startIdx = PATH.rfind(delimiter, 0, matchedIdx)
    if startIdx < 0:
        startIdx = 0
    else:
        # path will start with ':' otherwise
        startIdx += 1

    endIdx = PATH.find(delimiter, startIdx+1)
    if endIdx < 0:
        endIdx = len(PATH)

    goPath = PATH[startIdx:endIdx]
    return os.path.join(goPath,'go')


filePath = "??"
packagePath = "??"
projectBasePath="??"

goPath = getGoPath()
runFileTests(goPath, projectBasePath, packagePath, filePath)
runPackageTests(goPath, projectBasePath, packagePath)

