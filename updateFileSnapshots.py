import re
from typing import List

def findTestNames(filePath: str) ->List[str]:
    f = open(filePath, "r")
    # first let's collect names of the tests
    testNames = []
    for line in f:
        # \w matches word character: (characters from a to Z, digits from 0-9, and the underscore _ character)
        # brackets () capture a group
        testRegex = "^func (\w+).*testing.T"
        matched = re.search(testRegex, line)

        if matched is None:
            continue

        testName = matched.group(1)
        testNames.append(testName)

    return testNames


filePath = "??"

print(findTestNames(filePath))