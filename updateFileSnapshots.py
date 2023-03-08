import re
from typing import List
import os

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

def runTests(packagePath: str, testNames: List[str]):
    # to run all tests from a single file:
    #   go test -timeout 30s -run ^(TestName1|TestName2)$ current/package/path
    
    
    pass

# takes go path from PATH
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
    return goPath


filePath = "??"
packagePath = "??"

testNames = findTestNames(filePath)
if len(testNames) == 0:
    exit(0)

print(getGoPath())

# runTests(packagePath, testNames)