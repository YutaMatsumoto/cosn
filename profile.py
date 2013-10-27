#!/usr/bin/env python

# [19.7. xml.etree.ElementTree - The ElementTree XML API - Python v2.7.5 documentation] 
#   http://docs.python.org/2/library/xml.etree.elementtree.html#reference

import os
import xml.etree.ElementTree as ET

class Profile:

	profiles = None # root Element <profile>
	profiles_file = None

	def __init__(self, profile):
		# TODO IOError
		if profile is not None:
			# Case : If peer profile exists, just load it as Element
			if os.path.exists( profile ):
				self.profiles = ET.parse(profile).getroot()
			# Case : If peer profile does not exist, create it on the spot with empty content.
			else:
				self.profiles = ET.Element("profile")
				self.tostring()	
			# set up filename for the profile
			self.profiles_file = profile
		else:
			# TODO : Error handling in all the other functions if this is the case
			self.profiles = None

	def __del__(self):
		1
		# print "Profile __del__: implement flushing logic to profile." 
	
	@staticmethod
	def fromstring(xmlprofilestr):
		# Case : profile is string
		return ET.fromstring(xmlprofilestr)

	# TODO on phase2
	# def extend(self, xmlstring ):
	# 	print "Before ET.fromstring() : xmlstring is ", xmlstring
	# 	profile = ET.fromstring( xmlstring )
	# 	for version in profile.findall("versoin"):
	# 		profiles.insert( len(profiles), versoin )	
	# 	self.flush()

	# TODO on phase2
	# def flush(self):
	# 	f = open( self.profiles_file, "wr" )
	# 	f.write( self.tostring() )
	
	def get_profiles(self):
		return self.profiles

	def current_version_number(self):
		# TODO : Could be better to assume that the current version is the most recent version
		# TODO : Think about if the profile is not in good format. For example current_version tag is not there.
		current_version = self.profiles.find("current_version")
		current_version_number = current_version.text
		return int(current_version_number)

	def versions_between(self, low, high):
		profiles = []
		profile_history = self.get_profiles()
		for ver in profile_history.findall("version"):
			version_number = int( ver.attrib["id"] )
			if version_number < low :
				continue
			elif version_number > high:
				continue
			profiles.append(ver)
		wrap = ET.Element('profile')
		for profile in profiles:
			wrap.insert(len(wrap), profile)
		p = Profile(None)
		p.profiles = wrap
		return p

	def tostring(self):
		return ET.tostring( self.profiles )

if __name__ == "__main__":
	p = Profile("profile.xml")
	print "Current Version is " + str(p.current_version_number())
	print p.versions_between(1,3).tostring()
	p = Profile.fromstring("<profile></profile>")
	print p.tostring()
