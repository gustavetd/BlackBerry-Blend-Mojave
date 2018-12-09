#!/usr/bin/python2.6

import subprocess
import os.path
import sys
import errno
import plistlib
from optparse import OptionParser

ref_plist_path="/Library/Application Support/BlackBerry/com.BlackBerry.drivers.refcount.plist"

def main():
    parser = OptionParser(usage="usage: %prog --[add|remove|info] --component=DRIVER_COMPONENT [--identifier=BUNDLE_IDENTIFIER]", version="%prog 2.0")
    parser.add_option("--add", action="callback", callback=add_reference_cb, help="Add Reference Count")
    parser.add_option("--remove", action="callback", callback=remove_reference_cb, help="Remove Reference Count")
    parser.add_option("--info",  action="callback", callback=info_reference_cb, help="Get Information about the references of a given component")
    parser.add_option("--identifier", action="store", dest="bundle_id", help="Your bundle Identifier")
    parser.add_option("--component", action="store", dest="driver_component", help="The Mac driver bundle your component depends on")
    parser.parse_args()

def validate_driver_component(drv):
	valid_components = [ 'usbdriver-mac', 
						 'usbfw-mac',  
						 'tundrv-mac',
						 'tunmgr-peermgr-mac',
						];
	if drv in valid_components:
		return True;
	
	print "Invalid Driver Component"
	print "Valid Components Are:"
	for component in valid_components:
		print component
	return False

def refcount_plist_exists():
	if os.path.isfile(ref_plist_path):
		#Must be root to validate plist on disk because it is located under '/Library/Application Support'
		cmd = 'plutil ' + '\"' + ref_plist_path + '\"'
		plcmd = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
		for line in iter(plcmd.stdout.readline,''):
			if "OK" in line.rstrip():
				return True
	return False

def add_reference_cb(driver_component, bundle_id):
	if not validate_driver_component(driver_component):
		return
	
	if refcount_plist_exists():
		pl = plistlib.readPlist(ref_plist_path);
		component_dict = pl.get(driver_component,{})
		if not component_dict.get(bundle_id, False):
			component_dict[bundle_id]=True;
			pl[driver_component]=component_dict;
			plistlib.writePlist(pl, ref_plist_path);
		
	else:
		#Create a new plist dictionary with the bundle identifier
		component_dict = {bundle_id: True}
		pl = { driver_component : component_dict }
		plistlib.writePlist(pl, ref_plist_path);

def remove_reference_cb(driver_component, bundle_id):
	if not validate_driver_component(driver_component):
		return
	
	if not refcount_plist_exists():
		return
		
	#Read the Plist
	pl = plistlib.readPlist(ref_plist_path);
	component_dict = pl.get(driver_component,{})
	if component_dict:
		if bundle_id in component_dict:
			del component_dict[bundle_id]
			pl[driver_component] = component_dict;
			plistlib.writePlist(pl, ref_plist_path);		
		
	
def info_reference_cb(option, opt_str, value, parser):
	(args, options) = parser.parse_args(parser.rargs)
	
	if not validate_driver_component(args.driver_component):
		return

	if not refcount_plist_exists():
		print "User has Deleted Reference Counting Data stored in " + ref_plist_path
		return
	
	#Read the Plist
	pl = plistlib.readPlist(ref_plist_path);
	component_dict = pl.get(args.driver_component,{})
	if component_dict:
		print "Component is Referenced By:"
		for key in component_dict.iterkeys():
			print key
	else:
		print "Component is Not Referenced"
	
if __name__ == '__main__':
	main()

