#!/usr/bin/python
"""
    Read DetectX Results and report any last scan date

    Results:
    '' (empty string): RESULTFILE was not found or not readable. Implies a search
    has not yet been run, or the results were invalid JSON.
    'None': The DetectX search was run, but did not find any infections.
    (list): A list of detected infections (file paths)
    """


import os
import json


# Path to DetectX Result file
RESULTFILE = '/Library/Application Support/JAMF/Addons/DetectX/results.json'


def decode_results(path):
    """Decodes the JSON object at path 'path' and returns a list of discovered
        infections"""
    searchdate = []
    try:
        with open(path, 'r') as data:
            try:
                results = json.load(data)
                searchdate = results['searchdate']
            except (KeyError, ValueError):
                pass
    except (OSError, IOError):
        pass
    return searchdate


def main():
    """Main"""
    if os.path.exists(RESULTFILE):
        searchdate = decode_results(RESULTFILE)
        if len(searchdate) > 0:
            EA = searchdate[:-14]
        else:
            EA = 'None'
    else:
        EA = ''
    print ('<result>%s</result>' % EA)


if __name__ == '__main__':
    main()
