#!/usr/bin/env python

import os
import xml.etree.ElementTree as ET

class CosnLocation:

	#
	# Example

	#
	# <content>
	# 	<addres>
	#		<ID>mgunes</ID>
	# 		<IP>192.168.1.1</IP>
	# 		<port>1234</port>
	# 		<time>10/23/2013 1:00pm</time>
	# 	</addres>
	# 	<links>
	# 		<public>https://dl.dropboxusercontent.com/s/3dahjwr8yhpriqf/publicProfile.xml</public>
	# 		<content>https://dl.dropboxusercontent.com/s/bjyk4pawkobu9d1/content.xml</content>
	# 		<time>10/23/2013 1:10pm</time>
	# 	</links>
	# </content>
	#

	def __init__(self,location_file):
		# 
		# Assume flie exists
		#
		# self.filepath = location_file
		# content = root.find("ID")
		# print content.text
		# ET.dump( content )
		# content.find("addres")
		1

	def set_dict(self, locdict):
		self.locdict = locdict
	
	def get_dict(self):
		return self.locdict

		# root = ET.parse(self.filepath).getroot()
		# f = open(self.filepath, 'r')
		# location_in_dict = self.parse( f.read() )
		# f.close()
		# return location_in_dict

	@staticmethod 
	def parse(xmlstr):
		root = ET.fromstring(xmlstr)
		addr = root.find("addres")
		id   = addr.find("ID")
		ip   = addr.find("IP")
		port = addr.find("port")
		address_update_time = addr.find("time")

		links = root.find("links")
		public  = links.find("public")
		content = links.find("content")
		link_update_time = links.find("time")

		# TODO
		# It is better to return instance of CosnLocation which has methods to
		# get all these attributes since using string on a dictionary is
		# error-prone.
		return {\
			"ID" :id.text, 
			"IP" :ip.text ,
			"port" :port.text,
			"time":address_update_time.text,
			"public" :public.text ,
			"content":content.text,
			"link_update_time":link_update_time.text
		}

		
		
if __name__ == "__main__":


	#
	# from string
	#
	location_xml = open("location.xml").read()
	location = CosnLocation.parse(location_xml)
	print location
	
	

	#
	# from file
	#
	# location = CosnLocation("location.xml")
	# print location.get_dict()
	


