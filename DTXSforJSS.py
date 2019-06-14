#!/usr/bin/python
"""
Run DetectX Search and update EA's via JSS API

Jamf Parameters:
4- JSS address
5- API Auth (encoded)
6- EAID # (date)
7- EAName (date)
8- EAID # (issues)
9-EAName (issues)
10- EAID # (infections)
11- EAName (infections)

Results:
'' (empty string): RESULTFILE was not found or not readable. Implies a search
                   has not yet been run, or the results were invalid JSON.
None': The DetectX search was run, but did not find any infections.
list): A list of detected infections (file paths)
"""


import os
import json
import sys
import httplib
import subprocess
import objc
from Foundation import NSBundle
from distutils.version import LooseVersion
from CoreFoundation import CFPreferencesCopyAppValue

# Full path to DetectX Swift.app
DX = "/Applications/Utilities/DetectX Swift.app"
# Full path to output file for writing results
RESULTFILE = "/Library/Application Support/JAMF/Addons/DetectX/results.json"
# Minimum version of DetectX Swift
# nb: version 0.108 is required for single-user scanning
# version 0.110 is required for scanning all login users on the system
MINIMUM_VERSION = "1.073"
# Jamf policy custom trigger to run if DetectX is not found
JAMF_TRIGGER = "InstallDetectX"

def check_detectx_version():
    """Returns boolean whether or not the installed version of DetectX meets or
        exceeds the specified MINIMUM_VERSION"""
    result = False
    plist = os.path.join(DX, 'Contents/Info.plist')
    if os.path.exists(plist):
        installed_version = CFPreferencesCopyAppValue('CFBundleVersion', plist)
        if LooseVersion(installed_version) >= LooseVersion(MINIMUM_VERSION):
            result = True
    return result

def run_detectx_search():
    """Runs a DetectX Search"""
    # Ensure path to RESULTFILE exists
    if not os.path.exists(RESULTFILE):
        directory = os.path.dirname(RESULTFILE)
        if not os.path.exists(directory):
            os.makedirs(directory)
    # Run the DetectX search
    try:
        exe = os.path.join(DX, 'Contents/MacOS/DetectX Swift')
        cmd = [exe, 'search', '-aj', RESULTFILE]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        if stdout:
            print stdout
    except (IOError, OSError) as e:
        print e
    except subprocess.CalledProcessError as e:
        print e
    return True if proc.returncode == 0 else False

def run_jamf_policy(p):
    """Runs a jamf policy by id or event name"""
    cmd = ['/usr/local/bin/jamf', 'policy']
    if isinstance(p, basestring):
        cmd.extend(['-event', p])
    elif isinstance(p, int):
        cmd.extend(['-id', str(p)])
    else:
        raise TypeError('Policy identifier must be int or str')
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = proc.communicate()
    result_dict = {
        "stdout": out,
        "stderr": err,
        "status": proc.returncode,
        "success": True if proc.returncode == 0 else False
    }
    return result_dict

# Get UUID for EA update
IOKit_bundle = NSBundle.bundleWithIdentifier_('com.apple.framework.IOKit')

functions = [("IOServiceGetMatchingService", b"II@"),
             ("IOServiceMatching", b"@*"),
             ("IORegistryEntryCreateCFProperty", b"@I@@I"),
            ]

objc.loadBundleFunctions(IOKit_bundle, globals(), functions)

def io_key(keyname):
    return IORegistryEntryCreateCFProperty(IOServiceGetMatchingService(0, IOServiceMatching("IOPlatformExpertDevice".encode("utf-8"))), keyname, None, 0)

def get_hardware_uuid():
    return io_key("IOPlatformUUID".encode("utf-8"))

print get_hardware_uuid()

# Setup Jamf API calls
def jssAPICall(payload):
    conn = httplib.HTTPSConnection(sys.argv[4])

    headers = {
    'Content-Type': "application/xml",
    'Accept': "application/xml",
    'authorization': 'Basic '+sys.argv[5]
    }

    conn.request("PUT", "/JSSResource/computers/udid/"+get_hardware_uuid()+"/subset/extension_attributes", payload, headers)

    res = conn.getresponse()
    data = res.read()


    print(data.decode("utf-8"))


def decode_results(path, section):
    """Decodes the JSON object at path 'path' and returns a list of discovered
    infections"""
    results = []
    try:
        with open(path, 'r') as data:
            try:
                jsonResults = json.load(data)
                print (section)
                results = jsonResults[section]
                print (results)

            except (KeyError, ValueError):
                pass
    except (OSError, IOError):
        pass
    return results

def eaValUpdateDate(section):
    if os.path.exists(RESULTFILE):
        dtxsresult = decode_results(RESULTFILE, section)
        if len(dtxsresult) > 0:
            EA = dtxsresult[:-14]
        else:
            EA = 'None'
    else:
        EA = ''
    return EA

def eaValUpdate(section):
    if os.path.exists(RESULTFILE):
        dtxsresult = decode_results(RESULTFILE, section)
        if len(dtxsresult) > 0:
            EA = '\n'.join(dtxsresult)
        else:
            EA = 'None'
    else:
        EA = ''
    return EA

def main():
    """Main"""
    # Check if DetectX is installed at path 'DX'
    if not os.path.exists(DX):
        install_via_policy = run_jamf_policy(JAMF_TRIGGER)
        if not install_via_policy['success'] or not os.path.exists(DX):
            print ("DetectX was not found at path '{}' and could not be "
                   "installed via Jamf trigger '{}'".format(DX, JAMF_TRIGGER))
            sys.exit(1)
        else:
            print ("DetectX was installed via Jamf trigger "
                   "'{}'".format(JAMF_TRIGGER))
    # Check if installed DetectX meets minimum version requirement
    if not check_detectx_version():
        print ("The installed version of DetectX does not meet the "
               "minimum required version {}.".format(MINIMUM_VERSION))
        print ("Attempting to update...")
        if not run_jamf_policy(JAMF_TRIGGER)['success'] or not check_detectx_version():
        	print ("Unable to install or update DetectX Swift; exiting.")
        	sys.exit(1)
    # Run DetectX Search
    detectx_search = run_detectx_search()
    if detectx_search:
        print "DetectX search complete."
        print "Results available at {}".format(RESULTFILE)

    else:
        print "An error occurred during the DetectX search."
        sys.exit(1)
    # Start updating EA's
    jssAPICall("<computer><extension_attributes><extension_attribute><id>"+sys.argv[6]+"</id><name>"+sys.argv[7]+"</name><value>"+eaValUpdateDate('searchdate')+"</value></extension_attribute></extension_attributes></computer>")
    jssAPICall("<computer><extension_attributes><extension_attribute><id>"+sys.argv[8]+"</id><name>"+sys.argv[9]+"</name><value>"+eaValUpdate('issues')+"</value></extension_attribute></extension_attributes></computer>")
    jssAPICall("<computer><extension_attributes><extension_attribute><id>"+sys.argv[10]+"</id><name>"+sys.argv[11]+"</name><value>"+eaValUpdate('infections')+"</value></extension_attribute></extension_attributes></computer>")
    sys.exit(0)

if __name__ == '__main__':
    main()
