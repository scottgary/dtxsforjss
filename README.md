# dtxsforjss
A Python script that will start a DetectX Swift search then update 3 Extension attributes (searchdate, issues, infections) via  Jamf API from results JSON. Using LaunchDaemon to call Jamf custom policy trigger we can have live return of results and notifications from jamf when something is found.

Setup DetectX Swift:
The search and update EA policy will cover install/reinstall of DetectX Swift if needed by trigger(InstallDetectX). That way if the user is able to remove the app and not the plist search the app will repopulate on next triggered scan. Install policy has dtxs registration, branded text, and plist load in postflight. Example of postflight for installer is:

```
#!/bin/sh
## postflight
##
## Not supported for flat packages.

# Register dtxs
/Applications/Utilities/DetectX\ Swift.app/Contents/MacOS/'DetectX Swift' register -key XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXX -email email@example.org

# Set BrandedText
defaults write /Library/Preferences/com.sqwarq.DetectX-Swift BrandedText "Example Branded Text"

# Set plist for execution
launchctl unload /Library/LaunchDaemons/com.jamfsoftware.dtxsforjss.plist
launchctl load /Library/LaunchDaemons/com.jamfsoftware.dtxsforjss.plist
```


Policy for Search:
Jamf policy for search should be set to Ongoing with only a custom trigger (default is "DTXS"). If adjusting custom trigger ensure you are adjusting the trigger within the plist to call your policy:
![JSSSearchPolicySetup](https://github.com/scottgary/dtxsforjss/blob/master/dtxsforjssPolicy.png)

Jamf Parameter Values:\
\
4- JSS address\
5- API Auth (base64 obscurity)\
6- EAID # (date)\
7- EAName (date)\
8- EAID # (issues)\
9-EAName (issues)\
10- EAID # (infections)\
11- EAName (infections)\
![JSSParameters](https://github.com/scottgary/dtxsforjss/blob/master/JSS%20Parameter%20Values.png)
  
**JSS Address** - The address of your JSS server followed by port. Typically on-prem will use **:8443** and Jamf Cloud will use **443**.\
**API Auth (base64 obscurity)** - Username and password of your api account and use openssl to convert them into a base64 string. To do this format your credentials as `apiuser:apipassword` (meaning a username and password together with a colon in the middle of an actual user account that can write with the API and run through terminal with `echo -n 'apiuser:apipassword' | openssl base64`. You'll get output in a long string, and that should be placed in Parameter 5 on your policy. This adds a layer of abstraction to your username/password string so it will require at least some effort for someone to determine what those credentials are besides just displaying them in plain text on your Jamf Pro server.\
**EAID # (date)** -the ID of the **date** extension attribute is displayed in the URL when you are looking at it in your Jamf Pro server. The URL will look something like https://acme.jamfcloud.com/computerExtensionAttributes.html?id=82&o=r. Grab that ID number and put it in parameter 6.\
**EAName (date)** -Whatever name you used for your EA should be entered here.\
**EAID # (issues)** - the ID of the **issues** extension attribute is displayed in the URL when you are looking at it in your Jamf Pro server. The URL will look something like https://acme.jamfcloud.com/computerExtensionAttributes.html?id=82&o=r. Grab that ID number and put it in parameter 8.\
**EAName (issues)** -Whatever name you used for your EA should be entered here.\
**EAID # (infections)** -the ID of the **infections** extension attribute is displayed in the URL when you are looking at it in your Jamf Pro server. The URL will look something like https://acme.jamfcloud.com/computerExtensionAttributes.html?id=82&o=r. Grab that ID number and put it in parameter 10.\
**EAName (infections)** -Whatever name you used for your EA should be entered here.\
