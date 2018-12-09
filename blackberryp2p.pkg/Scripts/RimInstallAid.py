#!/usr/local/bin/python2.7

import os
import sys
import stat
import pwd
import grp
import commands
import csv
import re
import string
import random

from CoreFoundation import CFPreferencesCopyValue
from CoreFoundation import CFPreferencesSetValue
from CoreFoundation import CFPreferencesSynchronize
from CoreFoundation import kCFPreferencesAnyUser
from CoreFoundation import kCFPreferencesCurrentHost

"""
Product IDs reference: 
-----------------------------------------------------------------------------------------------------------------------------
|		HEX		|	Decimal		|			Binary			| 			Device/State
|--------------------------------------------------------------------------------------------------
|    (Nessus)	|				|							|
| 	0x0001		|      	1		|	0000000000000001		|	Boot ROM mode, full-speed mode
| 	0x8001		| 	32769		|	1000000000000001		|	Boot ROM mode
| 	0x8004	 	| 	32772		|	1000000000000100		|	Composite BlackBerry and USB-MS Interfaces
| 	0x8006		| 	32774		|	1000000000000110		|	Serial Bypass (not used on Mac)
| 	0x8007		| 	32775		|	1000000000000111		|	MTP
|----------------------------------------------------------------------------------------------------------------------------
|      (QNX)	|				|							|
| 	0x8010		| 	32784		|	1000000000010000 		|	W1 with PB 1.x code - Connect to Win
| 	0x8011		| 	32785		|	1000000000010001 		|	W1 with PB 1.x code - Connect to Mac
| 	0x8012		| 	32786		|	1000000000010010		|	W2 or W1 with PB 2.x/BB10 code - Connect to Win
| 	0x8013		| 	32787		|	1000000000010011		|	W2 or W1 with PB 2.x/BB10 code - Connect to Mac
| 	0x8020		|	32800		|	1000000000100000		|	Original CD ROM mode
| 	0x8021		|	32801		|	1000000000100001		|	Forced upgrade CD ROM mode
|----------------------------------------------------------------------------------------------------------------------------
"""

# Helper Applications

# Returns a 16 digit random id
def peermanager_id_generator(size=16, chars=string.digits):
	return ''.join(random.choice(chars) for x in range(size))

# Returns the version of Device Manager that's installed on the user's machine 
# by reading the CFBundleVersion value in the Info.plist.
# For example, if Device Manager 2.3.0.68 is installed, then it'll return "203.00.68"
# (as that would be the formatting, as processed by SCM during an SCM build)
def getCFBundleVersionOfDeviceManager():

	shCmd = "defaults read /Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager.app/Contents/Info CFBundleVersion"
	deviceMngr_CFBundleVer = commands.getoutput(shCmd)
	
	# If Device Manager isn't installed on the user's machine, then we want to return 1 as the version number
	if (not (os.path.exists("/Library/Application Support/BlackBerry/BlackBerry Device Manager.app/"))):
		print "The directory /Library/Application Support/BlackBerry/BlackBerry Device Manager.app doesn't exist so Device Manager is not installed"
		deviceMngr_CFBundleVer = "1"
		
	if (deviceMngr_CFBundleVer.find("does not exist") != -1):
		print "The defaults CFBundleVersion entry does not exist in the file: /Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager.app/Contents/Info.plist"
		deviceMngr_CFBundleVer = "1"
	
	return str(deviceMngr_CFBundleVer)
	
# Returns the version of BlackBerry Link that's installed on the user's machine 
# by reading the CFBundleVersion value in the Info.plist.
# For example, if Device Manager 2.3.0.68 is installed, then it'll return "203.00.68"
# (as that would be the formatting, as processed by SCM during an SCM build)
def getCFBundleVersionOfBBLink():

	shCmd = "defaults read /Applications/BlackBerry\ Link.app/Contents/Info CFBundleVersion"
	bbLink_CFBundleVer = commands.getoutput(shCmd)
	
	# If BBLink isn't installed on the user's machine, then we want to return 1 as the version number
	if (not (os.path.exists("/Applications/BlackBerry Link.app/"))):
		print "The directory /Applications/BlackBerry Link.app doesn't exist so BlackBerry Link is not installed"
		bbLink_CFBundleVer = "1"
		
	if (bbLink_CFBundleVer.find("does not exist") != -1):
		print "The defaults CFBundleVersion entry does not exist in the file: /Applications/BlackBerry Link.app/Contents/Info.plist"
		bbLink_CFBundleVer = "1"
	
	return str(bbLink_CFBundleVer)

# This would augment the bundle number into a decimal 
# format that we can write as PBToolsInstalledVersion.
# For example, if "203.01.77" (2.3.1.77) was passed in, then it would return "33755213"
#
# The conversion works like this:
# 2.3.1.77 - SCM would write "203.01.77" as the CFBundleVersion in the plists
#
# 2 is the major version
# 3 is the minor version
# 1 is the dot/bugfix version
# 77 is the bundle number
#
# We have to write PBToolsInstallerVersion as:
#         2    3    1   77
#        --   --    -  ---
# HEX:   02   03    1  04D
# so  0x0203104D
# which is 33755213 in decimal
def augmentVersionOfDeviceMngrToDecimal(cfBundleVersion):

	# Eg. If the version is "2.3.1.77", then "203.01.77"
	# will get passed in as cfBundleVersion

	"""
	print "cfBundleVersion: " + cfBundleVersion
	"""

	# Error check: check that there are exactly 2 periods in the
	# string that was passed in (eg. "203.00.68")
	numDots = str(cfBundleVersion).count(".")
	if (numDots != 2):
		return "1"

	# No errors, so process the string
	versionSplit = (str(cfBundleVersion)).split(".")
	
	majorAndMinorVer 	= versionSplit[0]	# "203"
	bugFixVer 			= versionSplit[1]	# "00"
	bundleNum 			= versionSplit[2]	# "68"
	
	"""
	print "majorAndMinorVer : " + majorAndMinorVer
	print "bugFixVer        : " + bugFixVer
	print "bundleNum        : " + bundleNum
	"""
	
	# Split major and minor version. Eg.. "203"
	minorVersion = majorAndMinorVer[len(majorAndMinorVer)-2:] 	# "03"
	majorAndMinorVer = majorAndMinorVer[:len(majorAndMinorVer)-2]
	majorVersion = majorAndMinorVer								# "2"
	
	"""
	print "majorVersion : " + majorVersion
	print "minorVersion : " + minorVersion
	print "bugFixVer    : " + bugFixVer
	print "bundleNum    : " + bundleNum
	"""
	
	majorVersion_int 		= int(majorVersion)		#  3
	minorVersion_int 		= int(minorVersion)		#  2
	bugFixVer_int 			= int(bugFixVer)		#  1
	bundleNum_int 			= int(bundleNum)		# 77
	
	"""
	print "majorVersion_int : " + str(majorVersion_int)
	print "minorVersion_int : " + str(minorVersion_int)
	print "bugFixVer_int    : " + str(bugFixVer_int)
	print "bundleNum_int    : " + str(bundleNum_int)
	"""
	
	majorVersion_hex = hex(majorVersion_int)	# 0x3
	minorVersion_hex = hex(minorVersion_int)	# 0x2
	bugFixVer_hex = hex(bugFixVer_int)			# 0x1
	bundleNum_hex = hex(bundleNum_int)			# 0x4D
	
	"""
	print "majorVersion_hex     : " + str(majorVersion_hex)
	print "minorVersion_hex     : " + str(minorVersion_hex)
	print "bugFixVer_hex        : " + str(bugFixVer_hex)
	print "bundleNum_hex        : " + str(bundleNum_hex)
	"""
	
	# Now, let's concatenate it all together!
	# Figure A.    02         03         01       77    (in decimal)
	# Figure B.    02         03          1      04D      (in HEX)
	# Figure C.    0x0203104D   (Figure B. with the HEX numbers stringed together)
	# Figure D.    33755213     (Figure C converted from HEX to decimal)
	
	# Build Figure C.
	concatedHEX='%02X%02X%01X%03X' % (majorVersion_int, minorVersion_int, bugFixVer_int, bundleNum_int)

	"""
	print "concatedHEX: " + concatedHEX
	"""
	
	# Get the int of Figure C.	
	bundleVersionInt = int(concatedHEX, 16)
	
	"""
	print "bundleVersionInt: " + str(bundleVersionInt)
	"""
	
	return str(bundleVersionInt)


def getOtherScript(script):
	pathname = os.path.dirname(sys.argv[0])
	fullpath = os.path.abspath(pathname)
	return os.path.join(fullpath, script)

def getReferenceCountUtility():
	# Should be included in all packages scripts with this one... its a bug if its not
	pathname = os.path.dirname(sys.argv[0])
	fullpath = os.path.abspath(pathname)
	return os.path.join(fullpath, "BBInstallReferenceCount")

def getBBLaunchAgentUtility():
	# Can only be used in a post install env
	return "/Library/Application Support/BlackBerry/BBLaunchAgent.app"

# UID/GID's are used instead of names, we need to get UID/GID from actual names
def getUID(username):
	uid=0
	try:
		uid = pwd.getpwnam(username)[2]
	except KeyError, e:
		print "Error geting uid of " + str(username)
		sys.stdout.flush()
	return uid

def getGID(group):
	gid=0
	try:
		gid = grp.getgrnam(group)[2]
	except KeyError, e:
		print "Error getting gid of " + str(group)
		sys.stdout.flush()
	return gid


# Permission Settings
# Package Maker is suppose to do this, but due package maker issues
# we do this extra step now to be safe.. hopefully we can forgoe this oneday
# Radars are submitted and known
def setSystemFolderPermissions(path, uid, gid):
	dirPerm  = (stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IWGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
	os.chown(path, uid, gid)
	os.chmod(path, dirPerm)

def setSystemFilePermissions(path, uid, gid):
	execPerm = (stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
	os.chown(path, uid, gid)
	os.chmod(path, execPerm)

def setContainerPermissions(path, uid, gid, execDir=False, rootFolder=True):
	dirPerm  = (stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
	execPerm = (stat.S_IRUSR|stat.S_IWUSR|stat.S_IXUSR|stat.S_IRGRP|stat.S_IXGRP|stat.S_IROTH|stat.S_IXOTH)
	filePerm = (stat.S_IRUSR|stat.S_IWUSR|stat.S_IRGRP|stat.S_IROTH)
	setFolderPermissions(path, uid, gid, dirPerm, dirPerm, execPerm, filePerm, execDir, rootFolder)

def setFolderPermissions(path, uid, gid, rootPerm, dirPerm, execPerm, filePerm, execDir=False, rootFolder=True):

	if os.path.isfile(path):
			os.chown(path, uid, gid)
			os.chmod(path, filePerm)
			return

	if rootFolder == True:
			os.chown(path, uid, gid)
			os.chmod(path, rootPerm)

	for item in os.listdir(path):
			fullpath = os.path.join(path, item)
			os.lchown(fullpath, uid, gid)
			if os.path.isdir(fullpath):
				os.chmod(fullpath, dirPerm)
				if os.path.islink(fullpath):
					continue
				
				# Recurse if dir and not symbolic link
				if item == "MacOS" or (len(item) == 1 and os.path.basename(path) == "Versions"):
					setFolderPermissions(fullpath, uid, gid, rootPerm, dirPerm, execPerm, filePerm, True, False)
				else:
					setFolderPermissions(fullpath, uid, gid, rootPerm, dirPerm, execPerm, filePerm, False, False)
			elif os.path.isfile(fullpath) and execDir == True: 
				os.chmod(fullpath, execPerm)
			elif os.path.isfile(fullpath) and execDir == False:
                # Handle the special case for 10.5 on PPC where we need to put the transcoder into the
                # Resources folder of the RimMedia.framework dir
				if os.path.basename(fullpath) == "RimMediaQTTranscoder":
					os.chmod(fullpath, execPerm)
				else:
					os.chmod(fullpath, filePerm)
                


# Driver Requirements
def requireFW():
	execpath = getReferenceCountUtility().replace(" ", "\ ")
	cmd = execpath + " -referenceFW"
	os.system(cmd)

def requireDR():
	execpath = getReferenceCountUtility().replace(" ", "\ ")
	cmd = execpath + " -referenceDR"
	os.system(cmd)

def requireVSP():
	execpath = getReferenceCountUtility().replace(" ", "\ ")
	cmd = execpath + " -referenceVSP"
	os.system(cmd)

def requireVSPDR():
	execpath = getReferenceCountUtility().replace(" ", "\ ")
	cmd = execpath + " -referenceVSPDR"
	os.system(cmd)

"""
# Returns a string of the full command-line command to register an app for autolaunch based on the following flags:
#
# For example, if we want the following string to be returned by this function:
# "/Library/Application\ Support/BlackBerry/BBLaunchAgent.app -default -priority 10 -product 0x8011,0x8013 -atlogin -atwake -multi /Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager.app -guid %guid -pid %pid"
# then we would pass in the following:
#
# -----------------------------------------------------------------------------------------------------------------------------------
# |			Flag			|    Value
# -----------------------------------------------------------------------------------------------------------------------------------
# | 	priority			| 	"10" 																		(optional)
# |		productIDs			|	"0x8011,0x8013"																(optional)
# | 	atlogin				|	True																		(optional)
# | 	atwake				|	True																		(optional)
# | 	multi				|	True																		(optional)
# | 	whennotrunning		|	"com.rim.blackberrydesktopmanager" 											(optional)
# | 	execPath			|   "/Library/Application Support/BlackBerry/BlackBerry Device Manager.app"		(mandatory)
# | 	execArgs			|   "guid %guid -pid %pid"														(optional)
# -----------------------------------------------------------------------------------------------------------------------------------
def registerAutolaunchAppCmd(execPath, execArgs=None, priority=None, productIDs=None, atlogin=None, atwake=None, multi=None, whennotrunning=None):
	# We assume that the supplied executable path is NOT escaped yet
	execPathEscaped = execPath.replace(" ", "\ ")
	launchAgentUtility = "/Library/Application Support/BlackBerry/BBLaunchAgent.app".replace(" ", "\ ")

	# Register system-wide
	cmd = launchAgentUtility + " -default "

	# Tack on the optional paramaters
	if (priority):
		cmd = cmd + " -priority " + str(priority) + " "
	if (productIDs):
		cmd = cmd + " -product " + str(productIDs) + " "
	if (atlogin):
		cmd = cmd + " -atlogin "
	if (atwake):
		cmd = cmd + " -atwake "
	if (multi):
		cmd = cmd + " -multi "
	if (whennotrunning):
		cmd = cmd + " -whennotrunning " + str(whennotrunning)

	# Path to the executable app to launch
	cmd = cmd + " " + execPathEscaped

	# Arguments for the executable app to launch
	if (execArgs):
		cmd = cmd + " " + execArgs

	return cmd


# Returns a string of the full command-line command to unregister an app from autolaunch
#
# For example, if we want the following string to be returned by this function:
# "/Library/Application\ Support/BlackBerry/BBLaunchAgent.app -ndefault /Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager.app"
# then we would pass in the following:
#
# -----------------------------------------------------------------------------------------------------------------------------------
# |			Flag			|    Value
# -----------------------------------------------------------------------------------------------------------------------------------
# | 	execPath			|   "/Library/Application Support/BlackBerry/BlackBerry Device Manager.app"		(mandatory)
# -----------------------------------------------------------------------------------------------------------------------------------
def unregisterAutolaunchAppCmd(execPath):
	# We assume that the supplied executable path is NOT escaped yet
	execPathEscaped = execPath.replace(" ", "\ ")
	launchAgentUtility = "/Library/Application Support/BlackBerry/BBLaunchAgent.app".replace(" ", "\ ")

	# Unregister system-wide
	cmd = launchAgentUtility + " -ndefault "

	# Path to the executable app to launch
	cmd = cmd + " " + execPathEscaped

	return cmd


"""
### Register BDM autolaunch (for BB10 devices)
def registerBBDeviceManagerAutoLaunch():
	pathToLuaScript				= "/Library/Application Support/BlackBerry/com.rim.blackberrydevicemanager.lua"
	registrationBundleID		= "com.rim.blackberrydevicemanager.lua"
	registerAutolaunchWithLuaScript(pathToLuaScript, registrationBundleID)
	
# Register BBLink autolaunch (for BB10 devices)
def registerBBLinkAutoLaunch():
	pathToLuaScript 			= '/Library/Application Support/BlackBerry/com.rim.blackberrylink.lua'
	registrationBundleID 		= 'com.rim.blackberrylink.lua'
	registerAutolaunchWithLuaScript(pathToLuaScript, registrationBundleID)

# Register DTS autolaunch (for BBOS devices and PBOS 1.0)
def registerDTSAutoLaunch():
	pathToLuaScript 			= '/Library/Application Support/BlackBerry/com.rim.blackberrydesktopmanager.lua'
	registrationBundleID 		= 'com.rim.blackberrydesktopmanager.lua'
	registerAutolaunchWithLuaScript(pathToLuaScript, registrationBundleID)


# Register OOBE app autolaunch (for 0x8021 devices)
def registerOOBEAutoLaunch():
	pathToLuaScript 			= '/Library/Application Support/BlackBerry/com.rim.pbcdautolauncher.lua'
	registrationBundleID 		= 'com.rim.pbcdautolauncher.lua'
	registerAutolaunchWithLuaScript(pathToLuaScript, registrationBundleID)







"""
### Unregister SAAM autolaunch
def unregisterBBDeviceManagerAutoLaunch():
	autolaunchApp				= "/Library/Application Support/BlackBerry/BlackBerry Device Manager.app"
	cmd = unregisterAutolaunchAppCmd(autolaunchApp)
	print "Unregister SAAM autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)






### Register SAAM2 autolaunch
def registerBBDeviceManager2AutoLaunch():
	
	# Create a symlink:
	# /Library/Application Support/BlackBerry/BlackBerry Device Manager.app ---->
	# /Library/Application Support/BlackBerry/BlackBerry Device Manager2.app
	
	symLinkSource = "/Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager.app"
	symLinkTarget = "/Library/Application\ Support/BlackBerry/BlackBerry\ Device\ Manager2.app"


	createSymLinkCmd = "/bin/ln -s " + symLinkSource + " " + symLinkTarget
	if not (os.path.exists(symLinkTarget)):
		print "Creating symlink: " + createSymLinkCmd
		sys.stdout.flush()
		os.system(createSymLinkCmd)
	
	# Now, do the registration:	
	autolaunchApp				= "/Library/Application Support/BlackBerry/BlackBerry Device Manager2.app"
	autolaunchAppArgs			= "-guid %guid -pid %pid"
	autolaunchPriority			= "10"
	autolaunchProductIDs		= "0x8021"
	autolaunchWhennotrunning	= None
	autolaunchAtLogin			= True
	autolaunchAtWake			= False
	autolaunchMulti				= True

	cmd = registerAutolaunchAppCmd(execPath=autolaunchApp, execArgs=autolaunchAppArgs, priority=autolaunchPriority, productIDs=autolaunchProductIDs, atlogin=autolaunchAtLogin, atwake=autolaunchAtWake, multi=autolaunchMulti, whennotrunning=autolaunchWhennotrunning)
	print "Register SAAM2 autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)

### Unregister SAAM2 autolaunch
def unregisterBBDeviceManager2AutoLaunch():
	autolaunchApp				= "/Library/Application Support/BlackBerry/BlackBerry Device Manager2.app"
	cmd = unregisterAutolaunchAppCmd(autolaunchApp)
	print "Unregister SAAM2 autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)

### Unregister SAAM3 autolaunch
def unregisterBBDeviceManager3AutoLaunch():
	autolaunchApp				= "/Library/Application Support/BlackBerry/BlackBerry Device Manager3.app"
	cmd = unregisterAutolaunchAppCmd(autolaunchApp)
	print "Unregister SAAM3 autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)



### Register Desktop 10 autolaunch
def registerDT10AutoLaunch():
	autolaunchApp				= "/Applications/Desktop 10.app"
	autolaunchAppArgs			= "-guid %guid -pid %pid"
	autolaunchPriority			= "5"
	autolaunchProductIDs		= None
	autolaunchWhennotrunning	= None
	autolaunchAtLogin			= True
	autolaunchAtWake			= False
	autolaunchMulti				= False

	cmd = registerAutolaunchAppCmd(execPath=autolaunchApp, execArgs=autolaunchAppArgs, priority=autolaunchPriority, productIDs=autolaunchProductIDs, atlogin=autolaunchAtLogin, atwake=autolaunchAtWake, multi=autolaunchMulti, whennotrunning=autolaunchWhennotrunning)
	print "Register DTS autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)
	
### Unregister Desktop 10 autolaunch
def unregisterDT10AutoLaunch():
	autolaunchApp				= "/Applications/Desktop 10.app"
	cmd = unregisterAutolaunchAppCmd(autolaunchApp)
	print "Unregister DTS autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)
	


### Register DTS autolaunch
def registerDTSAutoLaunch():
	autolaunchApp				= "/Applications/BlackBerry Desktop Software.app"
	autolaunchAppArgs			= "-guid %guid -pid %pid"
	autolaunchPriority			= "5"
	autolaunchProductIDs		= "0x0001,0x8001,0x8004,0x8006,0x8007,0x8011"
	autolaunchWhennotrunning	= None
	autolaunchAtLogin			= True
	autolaunchAtWake			= False
	autolaunchMulti				= False

	cmd = registerAutolaunchAppCmd(execPath=autolaunchApp, execArgs=autolaunchAppArgs, priority=autolaunchPriority, productIDs=autolaunchProductIDs, atlogin=autolaunchAtLogin, atwake=autolaunchAtWake, multi=autolaunchMulti, whennotrunning=autolaunchWhennotrunning)
	print "Register DTS autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)

### Unregister DTS autolaunch
def unregisterDTSAutoLaunch():
	autolaunchApp				= "/Applications/BlackBerry Desktop Software.app"
	cmd = unregisterAutolaunchAppCmd(autolaunchApp)
	print "Unregister DTS autolaunch (system-wide): " + cmd
	sys.stdout.flush()
	os.system(cmd)
"""

### Wipe old autolaunch registrations
def wipeLegacyAutolaunchRegistrations():
	RIMBBLaunchAgent = getBBLaunchAgentUtility().replace(' ','\ ')
	cmd = RIMBBLaunchAgent + " -wipelegacy "
	print "Wiping old autolaunch registrations with command: " + cmd
	os.system(cmd)

### New method (via lua scripts) of registering apps for autolaunch
### Paramaters: absolute path to the lua script, and bundle ID of the registration
def registerAutolaunchWithLuaScript(pathToLuaScript, registrationBundleID):

	if not os.path.isfile(pathToLuaScript):
		raise Exception("Lua script does not exist: " + pathToLuaScript)
		
	RIMBBLaunchAgent = getBBLaunchAgentUtility().replace(' ','\ ')
	cmd = RIMBBLaunchAgent + " -defaultlua " + pathToLuaScript.replace(' ','\ ') + " " + registrationBundleID.replace(' ','\ ')
	print "Registering autolaunch with lua script: " + cmd
	os.system(cmd)


def unregisterBBBMAutoLaunchHistorical(historicalPath):
	bbdmLaunchUtility = getBBLaunchAgentUtility().replace(" ", "\ ")
	cmd = bbdmLaunchUtility + " -ndefault " + historicalPath.replace(" ", "\ ")
	os.system(cmd)

def registerIPModem():
	ipModemPath = "/Library/Application\ Support/BlackBerry/IPModemPasswordDialog.app"
	bbdmLaunchUtility = getBBLaunchAgentUtility().replace(" ", "\ ")
	cmd = bbdmLaunchUtility + " -ripdefault " + ipModemPath
	os.system(cmd)

def unregisterIPModem():
	ipModemPath = "/Library/Application\ Support/BlackBerry/IPModemPasswordDialog.app"
	bbdmLaunchUtility = getBBLaunchAgentUtility().replace(" ", "\ ")
	cmd = bbdmLaunchUtility + " -ipndefault " + ipModemPath
	os.system(cmd)
	

# Returns true if the supplied package exists on the system
def pkgExists(pkgIdentifier):
	commandToRun = "pkgutil --pkgs"
	packagesOnSys = commands.getoutput(commandToRun)
	
	# will be -1 if it doesn't exist
	foundPackage = packagesOnSys.find(pkgIdentifier)
	return (foundPackage != -1)
	
# Given a package to forget, forget it using "pkgutil --forget <pkgToForget>"	
def forgetPackage(pkgToForget):
	print "Forgetting old package receipt: " + pkgToForget
	sys.stdout.flush()
	os.system("pkgutil --forget " + pkgToForget)
	
	
# This method is used to aid in determining whether we're upgrading or installing fresh.
# It writes to the defaults, whether each pkg is already installed on the machine or not
def writePkgIsUpgrading_DefaultsDict():
	
	# The Package Identifier for all of our sub-packages 
	USB_kxt_pkg_identifier = 'com.rim.drivers.BlackBerryUSBDriver.pkg'
	USB_fwk_pkg_identifier = 'com.rim.drivers.BlackBerryFrameworks.pkg'
	DTS_app_pkg_identifier = 'com.rim.desktop.BlackBerryLink.pkg'
	BDM_app_pkg_identifier = 'com.rim.desktop.BlackBerryDeviceManager.pkg'
	P2P_app_pkg_identifier = 'com.rim.p2p.peermgr'

	# Build an array of all of these identifiers
	listOfPkgs = []
	listOfPkgs.append(USB_kxt_pkg_identifier)
	listOfPkgs.append(USB_fwk_pkg_identifier)
	listOfPkgs.append(DTS_app_pkg_identifier)
	listOfPkgs.append(BDM_app_pkg_identifier)
	listOfPkgs.append(P2P_app_pkg_identifier)
	
	# Build the command to run
	dictString = ''
	
	for pkg in listOfPkgs:
		thePkgExists = pkgExists(pkg)
		addonStr = pkg + ' ' + "" + str(thePkgExists) + ""
		dictString = dictString + ' ' + addonStr + ' '
		#print addonStr
	
	cmd = '/usr/bin/defaults write com.rim.blackberrydesktopmanager.install pkgExists -dict ' + dictString
	
	# Run the command
	os.system(cmd)
	
def clearPkgIsUpgrading_DefaultsDict():
	cmd = '/usr/bin/defaults delete com.rim.blackberrydesktopmanager.install pkgExists'
	os.system(cmd)
	
def readPkgIsUpgrading_DefaultsDict(pkgIdentifier):
	
	cmd = '/usr/bin/defaults read com.rim.blackberrydesktopmanager.install pkgExists'
	output = commands.getoutput(cmd)
	
	
	# Process the string representing a dictionary into an actual dictionary
	output = output.replace('{','')
	output = output.replace('}','')
	output = output.replace(' = '," = '")
	output = output.replace('\n','')
	output = output.replace('"',"")	
	output = output.replace("'",'')
	output = output.replace(' ','')
	output = output.replace(';',";")
	output = rreplace(output, ';', '', 1)

	outputSplit = output.split(';')
	outputDict = {}
	
	pattern = re.compile('(.*)=(.*)')
	for line in outputSplit:
		
		match = pattern.match(line)
		if (match != None):
			key 	= match.group(1)
			value 	= match.group(2)
			
			outputDict[key] = (value == "True")

	return outputDict[pkgIdentifier]
	
	if (pkgIdentifier in outputDict):
		isInstalled = outputDict[pkgIdentifier]
		return isInstalled
	
	else:
		return False


def rreplace(s, old, new, occurrence):
	li = s.rsplit(old, occurrence)
	return new.join(li)


def get_preference_anyuser(preference_key, bundle_id):
    # Get the specified preference key from the specified preference
    # bundle ID for any user (current host) using CoreFoundation
    preference_value = CFPreferencesCopyValue(preference_key, bundle_id, kCFPreferencesAnyUser, kCFPreferencesCurrentHost)
    return preference_value

def set_preference_anyuser(preference_key, preference_value, bundle_id):
    # Set the specified preference key from the specified preference
    # bundle ID for any user (current host) to the specified value using CoreFoundation
    CFPreferencesSetValue(preference_key, preference_value, bundle_id, kCFPreferencesAnyUser, kCFPreferencesCurrentHost)
    CFPreferencesSynchronize(bundle_id, kCFPreferencesAnyUser, kCFPreferencesCurrentHost)


#def main():
#	uid = getUID("root")
#	gid = getGID("wheel")
#	path ="/Library/Frameworks/RimBlackBerryUSB.framework"
#	setContainerPermissions(path, uid, gid)
#	registerIPModem()
#	unregisterIPModem()
#
#if __name__ == "__main__":
#	main()		
