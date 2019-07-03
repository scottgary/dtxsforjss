#!/bin/bash
# Created by Scott Gary
# Version History:
#      6/17/19: function for jss api call
#      6/18/19: function for AppUpdate
#      6/19/19: function for checking jss values & fixed logging
# JSS Parameters:
#   $4- Log File Name (located in /private/var/log
#   $5- JSS server address
#   $6- API auth (base 64)
#   $7- EA ID # (date)
#   $8- EA ID # (Issues)
#   $9- EA ID # (infections)
###################################################################################
###################################################################################
# Global Vars:
LogName="$4"
JSSServer="$5"
APIAuth=$(openssl enc -base64 -d <<< "$6")
EADate="$7"
EAInfect="$8"
EAIssues="$9"


# Log all script output
LogPath=/private/var/log
if [ ! -d "$LogPath" ];then
mkdir /private/var/log
fi

# Set log filename and path
LogFile=$LogPath/"$LogName".log
function SendToLog ()
{

echo "$(date +"%Y-%b-%d %T") : $1" | tee -a "$LogFile"

}
#log separator
SendToLog "================Script start================"

# Check JSS Par Values:
#function CheckJssPar(){
  # CHECK TO SEE IF A VALUE WAS PASSED IN PARAMETER 4 AND, IF SO, ASSIGN TO "LogName"
#  if [ "$4" != "" ] && [ "$LogName" == "" ];then
#    LogName=$4
#  fi
#  # CHECK TO SEE IF A VALUE WAS PASSED IN PARAMETER 5 AND, IF SO, ASSIGN TO "apiPass"
#  if [ "$5" != "" ] && [ "$JSSServer" == "" ];then
#    JSSServer=$5
#  fi
  # CHECK TO SEE IF A VALUE WAS PASSED IN PARAMETER 6 AND, IF SO, ASSIGN TO "resetUser"
#  if [ "$6" != "" ] && [ "$APIAuth" == "" ];then
#    APIAuth=$6
#  fi
#}

function GetUserandUDID() {
  # Get Logged in User name
  loggedInUser=$(stat -f%Su /dev/console)
  SendToLog "$loggedInUser"
  # Get Logged in User UID
  loggedInUID=$(id -u "$loggedInUser")
  SendToLog "$loggedInUID"
  # Get UDID fro API
  getudid=$(/usr/sbin/system_profiler SPHardwareDataType | /usr/bin/awk '/Hardware UUID:/ { print $3 }')
  SendToLog "UDID identified for API call: $getudid"
  #if root quit
  if [[ "$loggedInUser" == "root" ]] && [[ "$loggedInUID" == 0 ]]; then
    echo "No user is logged in. Skipping display of notification until next run." && SendToLog "No user logged in, skipping"
    exit 0
  fi
}

#start DTXS scan
function dtxs() {
  /Applications/Utilities/DetectX\ Swift.app/Contents/MacOS/DetectX\ Swift search -aj > /Library/Application\ Support/JAMF/Addons/DetectX/results.json
  SendToLog "DTXS Search Started, results will be passed to /Library/Application\ Support/JAMF/Addons/DetectX/results.json"
  dtxsdate=$(date +"%Y-%m-%d")
  SendToLog "Searchdate: $dtxsdate"

}

# Lets try some python here.... yikes
function readJSON(){
python - $1 <<END
#!/bin/python
"""
Read DetectX Results and report any discovered infections

Results:
'' (empty string): RESULTFILE was not found or not readable. Implies a search
                   has not yet been run, or the results were invalid JSON.
'None': The DetectX search was run, but did not find any infections.
(list): A list of detected infections (file paths)
"""


import os
import json
import sys


# Path to DetectX Result file
RESULTFILE = '/Library/Application Support/JAMF/Addons/DetectX/results.json'


def decode_results(path, section):
    """Decodes the JSON object at path 'path' and returns a list of discovered
    infections"""
    results = []
    try:
        with open(path, 'r') as data:
            try:
                jsonResults = json.load(data)
                results = jsonResults[section]

            except (KeyError, ValueError):
                print (ValueError)
    except (OSError, IOError):
        print (IOError)
    return results


def main():
    """Main"""
    if os.path.exists(RESULTFILE):
        infections = decode_results(RESULTFILE, sys.argv[1])
        print (infections)
        if len(infections) > 0:
            EA = '\n'.join(infections)
        else:
            EA = 'None'
    else:
        EA = ''
    print (EA)


if __name__ == '__main__':
    main()

END
}

function JsonReturn(){
  issues=$(readJSON issues)
  infections=$(readJSON infections)
  SendToLog "Python run complete, JSON results are: Issues: $issues and Infections: $infections"
  issuecleanup=$(echo $issues | awk '{print $2}')
  infectcleanup=$(echo $infections | awk '{print $2}')
  SendToLog "Cleanup attempt made of json results: $issuecleanup ; $infectcleanup"

}

# Update JSS EA's
function JSSAPICall(){
    value="$2"
    eaID="$3"
    method="$1"
    curl -s -u "$APIAuth" "https://$JSSServer:443/JSSResource/computers/udid/$getudid/subset/extension_attributes" \
    -H "Content-Type: application/xml" \
    -H "Accept: application/xml" \
    -d "<computer><extension_attributes><extension_attribute><id>$eaID</id><value>$value</value></extension_attribute></extension_attributes></computer>" \
    -X "$method"
    SendToLog "EA # $eaID was $method new value is: $value"

}
# Are we updating Jamf EA's
#CheckJssPar
GetUserandUDID
dtxs
JsonReturn
JSSAPICall PUT $dtxsdate $EADate
JSSAPICall PUT $issuecleanup $EAIssues
JSSAPICall PUT $infectcleanup $EAInfect
SendToLog "Extension Attributes Updated with: $dtxsdate ; $issuecleanup ; $infectcleanup"
SendToLog "===========Script Exit==========="
exit 0
