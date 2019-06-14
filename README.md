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

Jamf Parameter Values:
4- JSS address
5- API Auth (base64 obscurity)
6- EAID # (date)
7- EAName (date)
8- EAID # (issues)
9-EAName (issues)
10- EAID # (infections)
11- EAName (infections)
