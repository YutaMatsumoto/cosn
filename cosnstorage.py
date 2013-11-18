# This class defines logic to create/update/store/retrieves files used by
# COSN. This class exists so that COSN can work with multiple cloud storage
# provider such as dropbox/google-drive/skydrive. This class as an argument of
# __init__ rereives a cloud-storage-class instance, which does basic cloud
# file io. The cloud-storage-class must implement the following python
# methods. 
#
#	download(filename)
#		donwload the file with the filename and return it in a string variable
#
#	upload(filename)
#		upload the file with the filename to the cloud storage.
#
#	fileexists(filename)
#		check if the file with the filename exists and return True/False
#
#	get_link(fname)
#		get public HTTP link to the file
#

# Possible Problems
#
#	Currently deleting location.xml before uploading a new one, but might
#	change the published link void. Should just change the file content.
#
#
#

import xml.etree.ElementTree as ET

class CosnStorage:

	__shared_state = {} # Borg Pattern variable; shared storage for all the instances
	inited = False
	cloud = None

	def __init__(self,cloud):
		self.__dict__ = self.__shared_state
		if CosnStorage.inited is False:
			CosnStorage.cloud = cloud
			CosnStorage.inited = True

	def location_fname(self):
		return "location.xml"

	def profile_fname(self):
		return "publicProfile.xml"

	def content_fname(self):
		return "content.xml"
			
	def	publish_location(self):
		CosnStorage.cloud.upload("location.xml")
	
	def create_profile(self):
		# Create initial profile. This should be used only when the user does
		# not already have the publicProfile.xml
		#
		# TODO : prompt for info
		# TODO : modify the skelton
		#
		s = """<?xml version="1.0" encoding="utf-8"?>
<profile>
	<info>
		<userid>mgunes</userid>
		<name>mehmet gunes</name>
		<city>reno</city>
		<languages>english;turkish;kurdish</languages>
		<time>10/23/2013 1:00pm</time>
	</info>
	<work-education>
		<employer>university of nevada, reno</employer>
		<college>isik university</college>
		<gradschool>southern methodist university;university of texas at dallas</gradschool>
	</work-education>
	<interests>
		<books>bursts: the hidden patterns behind everything we do;six degrees: the science of a connected age;toward a global civilization of love and tolerance</books>
		<music>sami yusuf;maher zain;baris manco;sivan perwer</music>
		<movies>shawshank redemption;memento;ice age;lord of the rings;heat</movies>
		<tvs>friends;the simpsons;battlestar galactica</tvs>
	</interests>
</profile>"""
		profile = self.profile_fname()
		with open(profile, "w") as f:
			f.write(s)
			f.close()

	def create_content(self):
		# Create initial content. This should be used only when the user does
		# not already have the publicProfile.xml
		#
		# TODO
		#
		s = """<?xml version="1.0" encoding="UTF-8"?>
<content>
	<!-- example
	<version id="1">
		<type>text</type>
		<tag>whatever,aiueo</tag>
		<time>10/23/2013 1:00pm</time>
		<info>Hello world.</info>
	</version>
	-->
</content>"""
		with open(self.content_fname(), "w") as f:
			f.write(s)
			f.close()

	def create_location(self, address):
		# Create location file with current IP address and port of the TCP
		# welcoming socket. The existing location file will be overwritten. The
		# file will be placed on the cwd of the applicaiton.

		location_path = "location.xml" # TODO
		with open(location_path, "w") as loc:
			s = """<?xml version="1.0" encoding="UTF-8"?>
<content>
	<addres>
		<ID>mgunes</ID>
		<IP>192.168.1.1</IP>
		<port>1234</port>
		<time>10/23/2013 1:00pm</time>
	</addres>
	<links>
		<public>https://www.dropbox.com/s/3dahjwr8yhpriqf/publicProfile.xml</public>
		<content>https://www.dropbox.com/s/bjyk4pawkobu9d1/content.xml</content>
		<time>10/23/2013 1:10pm</time>
	</links>
</content>"""
			loc.write(s)
			loc.close()

			location = ET.parse(location_path)
			locroot  = location.getroot()

			# Look into cloud for public profile and content
			#
			# check file existences for public-profile and content. 
			# If they do not exist create it on the spot,
			# Else get the URLs to those files and put into location file.
			#

			#
			# Set User ID
			#
			loc_addr = locroot.find("addres")
			loc_id	 = loc_addr.find("ID")
			uid = ""
			# TODO use user ID from location.xml if location.xml already exists
			while uid == "":
				uid = raw_input("Enter User ID without white space characters (64 characters at max): ")
			loc_id.text = uid

			#
			# Set IP, port, updated time
			#
			# TODO : ip is 127.0.1.1 but this should be the ip address given in the network
			# address = peer.address()
			loc_addr.find("IP").text = address["ip"]
			loc_addr.find("port").text = str(address["port"])
			loc_addr.find("time").text = "TODO"
					
			#
			# Set public profile, content, updated time
			#
			# TODO : public profile and content links from cloud provider
			#

			profile = self.profile_fname()
			if not self.cloud.fileexists( profile ):
				self.create_profile()
			self.cloud.upload( profile )
			profile_link = self.cloud.get_link( profile )

			content = self.content_fname()
			if not self.cloud.fileexists( content ):
				self.create_content()
			self.cloud.upload( content )
			content_link = self.cloud.get_link( content )

			updated_time = "TODO" # TODO

			loc_link = locroot.find("links")
			loc_link.find("public").text = profile_link
			loc_link.find("content").text = content_link
			loc_link.find("time").text   = updated_time

			# write to the local location.xml
			location.write(location_path)

			# publish location
			self.publish_location()

			return location_path
