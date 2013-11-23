#!/usr/bin/env python

# Overview
#
# This class implements what CosnStorage class requires for cloud storage with
# Dropbox.

# References
#
#	tutorial 
#		[Dropbox - Using the Core API](https://www.dropbox.com/developers/core/start/python)
#	core 
#		[dropbox.client - Dropbox documentation](https://www.dropbox.com/static/developers/dropbox-python-sdk-1.6-docs/index.html)
#	developer's forum
#		[API Development << Dropbox Forums](https://forums.dropbox.com/forum.php?id=5)

# Include the Dropbox SDK
import dropbox

# CosnDrop is a Class of Borg Pattern
class CosnDrop:
	__shared_state = {} # Borg Pattern variable; shared storage for all the instances
	app_key = '901n8puil18v082'
	app_secret = '4mtw3qyocnkj976'
	inited = None
	access_token_file = "dropbox_access_token"
	profiles = [ "location.xml", "publicProfile.xml", "content.xml" ] # should be defined in Peer and passed down to this class sinc these filenames are specific to the app but not specific to dropbox

	def save_token(self):
		f = open(CosnDrop.access_token_file, 'w')
		f.write(self.access_token)
		f.close()

	def get_token(self):
		try: 
			f = open(CosnDrop.access_token_file)
		except IOError:
			return ""
		return f.read()

	#
	# This constructor sets up a dropbox variable, self.client, and sets up
	# a OAuth token for cloud access.
	#
	# If the token for cloud access is on the local disk relative to the app
	# cwd, that token is used. Else we obtain a new token and store it on the
	# local disk, and that token will be used next time.
	def __init__(self):
		self.__dict__ = self.__shared_state
		token = self.get_token()
		if token != "":
			self.access_token = token
			self.client = dropbox.client.DropboxClient(self.access_token)
		elif CosnDrop.inited is None: 
			# Get your app key and secret from the Dropbox developer website
			flow = dropbox.client.DropboxOAuth2FlowNoRedirect(CosnDrop.app_key, CosnDrop.app_secret)
			# let user approve this app
			# SOMEDAY : set up server so that takes user to the authorization page automatically
			authorize_url = flow.start()
			print '1. Go to: ' + authorize_url
			print '2. Click "Allow" (you might have to log in first)'
			print '3. Copy the authorization code.'
			code = raw_input("Enter the authorization code here: ").strip()

			# This will fail if the user enters an invalid authorization code
			#
			# The access token is all you'll need to make API requests on behalf of this
			# user, so you should store it away for safe-keeping (even though we don't for
			# this tutorial). By storing the access token, you won't need to go through
			# these steps again unless the user reinstalls your app or revokes access via
			# the Dropbox website.
			#
			# TODO store access_token and user_id
			#
			self.access_token, self.user_id = flow.finish(code)
			self.save_token()

			# authorize our API calls and print account info
			self.client = dropbox.client.DropboxClient(self.access_token)
		else:
			return

		CosnDrop.inited = True

	def debug_print(self):
		print "===== Dropbox Account ====="
		self.print_linked_account()

	def print_linked_account(self):
		print 'linked account: ', self.client.account_info()
	
	def existences(self):
		# Return existences of cosn files in dictionary of filenames to boolean.
		#
		#	      filename       boolean
		#      { "location.xml": True/False, 
		#        "publicProfile.xml": True/False,
		#        "content.xml":True/False }
		#
		# The filenames are defined in the class variable : profiles
		#
		dic = {}
		for f in CosnDrop.profiles:
			dic[f] = fileexists(f)
		return dic

	def fileexists(self, filename):
		try:
			f = self.client.get_file('/'+filename)
		except dropbox.rest.ErrorResponse:
			# print "Error Finding the file in the cloud: " + filename
			return False
		return True

	def get_link(self, fname):
		# Make the file with fname in the dropbox shared and return the url of
		# the shared file. The sharability expires but very far in the future,
		# and should not be a problem.
		shareLink = self.client.share(fname, False)["url"]
		downloadableLink = shareLink.replace('www.dropbox.com', 'dl.dropboxusercontent.com', 1)
		return downloadableLink

	def upload(self, fname):
		# upload and share a file on the dropbox cloud. Overwrites existing
		# file if a file with the fname already exists.
		f = open(fname)
		path = '/'+fname
		response = self.client.put_file(path, f, True)
		return self.get_link(fname)
		# print "uploaded:", response

	def meta(self):
		# Listing folders
		folder_metadata = client.metadata('/')
		print "metadata:", folder_metadata

	def download(self, file):
		
		f = open( file, 'w' )
		f.write( self.client.get_file(file).read() )
		f.close()


