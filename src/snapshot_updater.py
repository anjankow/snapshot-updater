import glob
import re
from typing import List
import os
import subprocess

# Updates snapshots in the given package.
# Works only for snapshots created by https://github.com/allaboutapps/go-starter/blob/master/internal/test/helper_snapshot.go
# Runs the tests with TEST_UPDATE_GOLDEN=true. Then runs the tests again without updating the snapshots.
# projectBaseDir: absolute directory of the project
# packageDir: absolute directory of the package
# filePath: when given, only snapshots of the tests from this file will be updated. Should be an absolute path.
def update(projectBaseDir: str, packageDir: str, filePath: str='', verbose: bool=False):

    if not os.path.isdir(projectBaseDir):
        print('Project directory doesn\'t exist or is invalid: ', projectBaseDir)
        exit(1)

    if not os.path.isdir(packageDir):
        print('Package directory doesn\'t exist or is invalid: ', packageDir)
        exit(1)
    # relative package path is <go module name><package path relative to project base path>
    # for example `internal/util/db`
    relativePkgPath = packageDir.replace(projectBaseDir, '')
    print('Package relative path: ', relativePkgPath)

    if filePath != '':
        if not os.path.isfile(filePath):
            print('File doesn\'t exist: ', filePath)
            exit(1)
        if not filePath.endswith('_test.go'):
            print('File is not a go test file: ', filePath)
            exit(1)

    print()
    goPath = _getGoPath()
    modulePackagePath = _getModulePackagePath(projectBaseDir, relativePkgPath)

    print('Updating snapshots...')

    # run tests to update the snapshots
    _runTests(goPath, projectBaseDir, modulePackagePath, filePath,updateSnaphots=True, verbose=verbose)
    # tests should fail because of updated snapshots

    print()
    print('Running the tests again...')
    # and run the tests again
    _runTests(goPath, projectBaseDir, modulePackagePath, filePath,  updateSnaphots=False, verbose=verbose)
    # all should pass now


def _runTests(goPath: str, projectBasePath: str, modulePackagePath: str, filePath: str, updateSnaphots: bool, verbose=True):
    if filePath == '':
        _runPackageTests(goPath, projectBasePath, modulePackagePath, updateSnaphots, verbose)
    else:
        _runFileTests(goPath, projectBasePath, modulePackagePath, filePath, updateSnaphots, verbose)


# Finds all test names in a given file
# Warning: test names must conform to the regex:
#   '^func (\w+).*testing.T'
def _findTestNames(filePath: str) ->List[str]:
    with open(filePath, 'r') as f:
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


# Returns package path as required by the go test command
# packageRelPath: package path relative to the project base path
def _getModulePackagePath(projectBasePath: str, packageRelPath: str) -> str:
    moduleName = _getGoModuleName(projectBasePath)
    if moduleName.endswith('/'):
        moduleName = moduleName.rstrip('/')
    if packageRelPath.startswith('/'):
        packageRelPath = packageRelPath.lstrip('/')
    return moduleName + '/' + packageRelPath

# Gets go module name from go.mod file
def _getGoModuleName(projectBasePath: str) -> str:
    with open(os.path.join(projectBasePath, 'go.mod'), 'r') as f:
        for line in f:
            if line.startswith('module'):
                # module name is in the form of:
                # module module.name/goes/here
                return (line.split(' ')[-1]).strip()
        raise Exception('Module name not found')


# To run all tests from a single file:
#   go test -run ^(TestName1|TestName2)$ package/import/path
#
# goPath: path to go executable
# projectBasePath: absolute directory of the go.mod file
# modulePackagePath: package path relative to the projectBasePath prefixed with go module name
# filePath: absolute path of the file
def _runFileTests(goPath: str, projectBasePath: str, modulePackagePath: str, filePath: str,updateSnaphots: bool, verbose=True):
    # get test names from the file
    testNames = _findTestNames(filePath)
    testNamesStr = ""
    for name in testNames:
        testNamesStr+=name + '|'
    testNamesStr= testNamesStr.rstrip('|')

    # prepare command
    command = [f"{goPath}", "test","-v", "-run", f"^({testNamesStr})$", f"{modulePackagePath}"]
    if not verbose:
         command.remove("-v")

    p = subprocess.Popen(command,
                         cwd=projectBasePath,
                         env={**os.environ, 'TEST_UPDATE_GOLDEN': str(updateSnaphots).lower()})
    p.wait()


# to run package tests:
#   go test package/import/path
#
# goPath: path to go executable
# projectBasePath: absolute directory of the go.mod file
# modulePackagePath: package path relative to the projectBasePath prefixed with go module name
def _runPackageTests(goPath: str, projectBasePath: str, modulePackagePath: str, updateSnaphots: bool, verbose=True):
    command = [f"{goPath}", "test","-v", f"{modulePackagePath}"]
    if not verbose:
         command.remove("-v")

    p = subprocess.Popen(command,
                         cwd=projectBasePath,
                         env={**os.environ, 'TEST_UPDATE_GOLDEN': str(updateSnaphots).lower()})
    p.wait()


# takes go directory from PATH,
# returns path to the executable
def _getGoPath()-> str:
    PATH = os.getenv('PATH')
    searchStartIdx = 0
    while searchStartIdx < len(PATH):

        matchedIdx = PATH.find('go/bin', searchStartIdx)

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

        goDir = PATH[startIdx:endIdx]
        goPath = os.path.join(goDir,'go')
        if os.path.exists(goPath):
            # found! we can return
            return goPath

        # path doesn't exist? continue checking other PATH entries
        searchStartIdx = matchedIdx + 1
        continue
