#!/usr/bin/env python


import os
import xml.etree.ElementTree as ET

class CosnContent:

	def __init__(self,content_file, content_dict={}):
		# 
		# Assume content flie exists
		#
		self.root = ET.parse(content_file).getroot()
		self.filepath = content_file

	
	
	def elem_tag_text(self, tagstr, textstr):
		e = ET.Element(tagstr)
		e.text = textstr 
		return e

	# Insert an entry into the content file
	def insert(self, entry):	
		# Insert a <version> entry with the following
		#
		#	<type> : filtype such as image/text
		# 	<tag>  : tag given from the user about this file
		# 	<time> : time uploaded
		# 	<item> : http link to the 
		# 	<info> : info given from the user about this file
		#
		
		# TODO version number
		e = ET.Element("version")
		version_number = str( len(self.root.findall("version")) + 1 )
		e.attrib["id"] = version_number
		entry_type = ET.Element("type")
		entry_type.text = entry["type"] 
		e.append( self.elem_tag_text("type", entry["type"]) )
		e.append( self.elem_tag_text("tag", entry["tag"] ) )
		e.append( self.elem_tag_text("item", entry["item"]) )
		e.append( self.elem_tag_text("info", entry["info"]) )
		self.root.append(e)

		# TODO error handling

		f = open(self.filepath, "w")
		f.write(ET.tostring(self.root))
		f.close()

	@staticmethod
	def prompt():
		print("Enter Information for the File")
		e = {}
		e["type"] = raw_input("type of the file (ex. text/image): ") 
		e["tag"]  = raw_input("tag  separated by commas         : ")
		e["info"] = raw_input("info about the file              : ")	
		return e

	@staticmethod 
	def element_tag_text(e, tagstr):
		f = e.find(tagstr)
		if f is None:
			return ""
		else:
			return f.text

	@staticmethod
	def parse(xmlstr):
		root = ET.fromstring(xmlstr)
		entries = root.findall("version")
		contents = []
		for e in entries: 
			id = e.attrib["id"]
			type = CosnContent.element_tag_text(e, "type")
			time = CosnContent.element_tag_text(e, "time")
			info = CosnContent.element_tag_text(e, "info")
			tag  = CosnContent.element_tag_text(e, "tag")
			item = CosnContent.element_tag_text(e, "item")

			contents.append( {\
				"id":id	,
				"type":type	,
				"time":time	,
				"info":info	,
				"tag":tag	,
				"item":item	
			} )
		return contents

if __name__ == "__main__":
	# From String
	f = open("content.xml")
	content = f.read()
	print CosnContent.parse(content)

	# From File
	# content = CosnContent("content.xml")
	# entry = CosnContent.prompt()
	# entry["time"] = "some time"
	# entry["item"] = "http://blabla"
	# content.insert(entry)
