import glob
from urllib.parse import urljoin
from enum import Enum
import re
from typing import List
import os
import getpass
import subprocess

# Updates snapshots in the given package.
# Works only for snapshots created by https://github.com/allaboutapps/go-starter/blob/master/internal/test/helper_snapshot.go
# Changes the snapshotter's `Save` function to `SaveU` and runs the tests to update corresponding tests.
# Then changes it back to `Save` and runs the tests again.
# projectBasePath: absolute path of the project
# packageRelPath: package path relative to the project base path, for example `internal/package-name`
# filePath: when given, only snapshots of the tests from this file will be updated. Should be an absolute path.
def update(projectBasePath: str, packageRelPath: str, filePath: str='', verbose: bool=False):
    goPath = _getGoPath()
    modulePackagePath = _getModulePackagePath(projectBasePath, packageRelPath)
    absPackagePath = os.path.join(projectBasePath, packageRelPath)

    print('Updating snapshots...')
    # set snaphotter mode to UPDATE (SaveU)
    _setSnapshotterMode(True, absPackagePath, filePath)

    # run tests to update the snapshots
    _runTests(goPath, projectBasePath, modulePackagePath, filePath)
    # tests should fail because of updated snapshots

    print('Reverting test files changes...')
    # now unset UPDATE mode (set back to Save)
    _setSnapshotterMode(False, absPackagePath, filePath)

    print('Running the tests again...')
    # and run the tests again
    _runTests(goPath, projectBasePath, modulePackagePath, filePath, verbose)
    # all should pass now


def _runTests(goPath: str, projectBasePath: str, modulePackagePath: str, filePath: str, verbose=True):
    if filePath == '':
        _runPackageTests(goPath, projectBasePath, modulePackagePath, verbose)
    else:
        _runFileTests(goPath, projectBasePath, modulePackagePath, filePath, verbose)


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
def _runFileTests(goPath: str, projectBasePath: str, modulePackagePath: str, filePath: str, verbose=True):
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

    p = subprocess.Popen(command, cwd=projectBasePath)
    p.wait()


# to run package tests:
#   go test package/import/path
#
# goPath: path to go executable
# projectBasePath: absolute directory of the go.mod file
# modulePackagePath: package path relative to the projectBasePath prefixed with go module name
def _runPackageTests(goPath: str, projectBasePath: str, modulePackagePath: str, verbose=True):
    command = [f"{goPath}", "test","-v", f"{modulePackagePath}"]
    if not verbose:
         command.remove("-v")

    p = subprocess.Popen(command, cwd=projectBasePath)
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


# Snapshotter https://github.com/allaboutapps/go-starter/blob/master/internal/test/helper_snapshot.go
# In the test code `shapshotter.Save(t, resopose)` saves the response snapshot or, if snaphot exists already, compares it.
# Changing it to `snapshotter.SaveU(t, response)` updates the snapshot with the new response data and fails the test.
#
# If update param is true, this function finds all occurences of `.Save(t, [\w0-9]+)` and replaces it with `SaveU`.
# If set to false, `SaveU` is replaced by `Save`.
# The occurences are found within the given file or in the entire package, if file path is not empty.
def _setSnapshotterMode(update: bool, absPackagePath: str, filePath=''):
    files = []
    if filePath == '':
        for file in glob.glob(os.path.join(absPackagePath, '*_test.go')):
            print(file)
            files.append(file)
    else:
        files = [filePath]

    variants = ['Save', 'SaveU']
    if update:
        replacementVariant = 1
    else:
        replacementVariant = 0

    # \.Save\(t, [\w0-9]+\) or \.SaveU\(t, [\w0-9]+\)
    pattern = f'\.{variants[abs(replacementVariant-1)]}\(t, [\w0-9]+\)'

    for file in files:
        print('Processing file: ', file)
        content = []
        with open(file, 'r') as f:
            content = str(f.read()).splitlines()

        with open(file, 'w')as f:
            f.truncate()
            for line in content:
                x = re.search(pattern, line)
                if x is not None:
                    after = f'.{variants[replacementVariant]}('
                    before = f'.{variants[abs(replacementVariant-1)]}('
                    line = line.replace(before, after )
                f.write(line + '\n')
