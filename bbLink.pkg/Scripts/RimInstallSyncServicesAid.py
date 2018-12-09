#!/usr/bin/python2.6
"""
Created by Brandon Slack on 2010-10-08. (This is a bit of a quick hack :()
Copyright (c) 2010 Research In Motion. All rights reserved.
"""

import RimInstallAid
import sys
import os
import plistlib

def getSyncServiceUpdateUtility():
	# Should be included in all packages scripts with this one... its a bug if its not
	pathname = os.path.dirname(sys.argv[0])
	fullpath = os.path.abspath(pathname)
	return os.path.join(fullpath, "SyncClientUpdater")

def getAllUsers():
	usersRoot = "/Users/" # This should not be hardcoded :(
	potentialUserList = []
	for item in os.listdir(usersRoot):
		if os.path.isdir(os.path.join(usersRoot, item)) and (item !="Shared"):
			potentialUserList.append(item)
	return potentialUserList

def getPotentialBlackBerryUsers():
	usersRoot = "/Users/" # This should not be hardcoded :(
	potentialUserList = []
	blackBerryUserList = []
	for item in os.listdir(usersRoot):
		potentialUserList.append(item)
	for username in potentialUserList:
		blackberryPath = os.path.join(usersRoot, username, "Library/Application Support/BlackBerry Link")
		if os.path.exists(blackberryPath):
			blackBerryUserList.append(username)
	return blackBerryUserList

def getAutoLaunchSettingForUser(username):
	autolaunch = 1
	userprefPath = os.path.join("/Users/", username, "Library/Preferences/com.rim.blackberrydesktopmanager.plist")
	tempprefPath = "/tmp/com.rim.blackberrydesktopmanager.plist"
	if os.path.exists(userprefPath):
		os.system("rm -f " + tempprefPath)
		os.system("cp -f " + userprefPath + " " + tempprefPath)
		os.system("/usr/bin/plutil -convert xml1 %s" % tempprefPath)
		plistblob = plistlib.readPlist(tempprefPath)
		if "GenericDTMSettings" in plistblob:
			genericblob = plistblob.GenericDTMSettings
			if "AutomaticallyLaunchBlackBerryDesktop" in genericblob:
				autolaunchStr = genericblob.AutomaticallyLaunchBlackBerryDesktop
				if autolaunchStr == False:
					autolaunch = 0
		os.system("rm -f " + tempprefPath)
	return autolaunch

def getBlackBerryDevicesForUser(username):
	devicePins = []
	deviceXMLPath = os.path.join("/Users/", username, "Library/Application Support/BlackBerryDesktop/", "BlackBerryDesktopDeviceModel.plist")
	if os.path.exists(deviceXMLPath):
		plistblob = plistlib.readPlist(deviceXMLPath)
		if "allDevices" in plistblob:
			for device in plistblob.allDevices:
				if "pin" in device:
					devicePins.append(device.pin)
	return devicePins

def updateRimSyncServiceClients():
	clientUpdateUtilityPath = getSyncServiceUpdateUtility()
	blackberryUsers = getPotentialBlackBerryUsers()
	for user in blackberryUsers:
		cmd = "sudo -u " + user + " " + clientUpdateUtilityPath.replace(" ", "\ ")
		result = os.system(cmd)
		print result

def main():
	updateRimSyncServiceClients()

if __name__ == "__main__":
	main()	