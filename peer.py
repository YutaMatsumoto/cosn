#!/usr/bin/env python

#
# This class is a facade class of the peer which has both the client side and
# the server side logic of a COSN client.
#

import urllib2
from peerserver import *

from smtplib import *
from email.mime.text import MIMEText
import getpass

import xml.etree.ElementTree as ET

from cosnstorage import *
from cosndrop import *

# TODO clean up
from cosn_log import *
from chatscreen import *
from functools import wraps
from profile import *
from socket import *
import errno
import os
import signal
import sys
import threading
import time
from common import *




class Peer(threading.Thread):

	debug = True

	# About This Client, which servs as a peer server (ps) as well.
	uid = -1 # user ID of this client, registered on the central server
	chat_screen = ChatScreen()
	profile = None

	# Peer Connection Variables
	chat_counter = 0 # TODO per client
	peer_profile = None # Element
	posted_files = []

	
	# ------------------------------------------------------------------------
	# Debug
	def debug_print(self):
		print "====================Debug"
		print self.uid
		print self.server.address()
	
	# ------------------------------------------------------------------------
	# Cloud Facade
	def upload(self,path):
		link = self.cloud.upload(path)
		print "Uploaded " + path + " to " + link 

	# ------------------------------------------------------------------------
	# user interface
	def ui(self):

		# peer.friend_request("kazuki_meada@yahoo.com")
		while True:
			# Prompt for peer to connect to and get the ip and port of tcp socket of the peer.
			# Prompt for what to do
			while True:
				print "What would you like to do?"
				print "1. Chat"
				print "2. File Upload"
				print "3. Initiate Friendship"
				print "4. Confirm Friendship"
				option = raw_input( "Please enter number > " )

				# Do CHAT
				peers = self.peers
				if option == str(1):
					if len(peers)<1:
						print "You don't even have a friend :("
					else:
						print "==== Friend Name List ===="
						for uid in peers: 
							print uid
						match = False
						print "=========================="
						print "Enter the name of the friend. Enter done when done. "
						print
						done_chatting = False
						counter = 1
						while True:
							counter += 1
							while not match:
								uid = raw_input("To Whom: ")
								match = uid in peers
								if uid == "done": 
									done_chatting = True	
									break
							message=""
							while len(message) <= 0:
								message = raw_input("Message: ")
								if message == "done":
									uid = ""	
									match = False
							reply = self.peer_chat( uid, message )
							if done_chatting == True:
								break

					# reply = reply.split()[0] 
					# # reply_peer = reply.split()[1] 
					# if reply == "CONFIRM":
					# 	while True:	
					# 		message = raw_input("Enter Message to Send > ")
					# 		reply = self.peer_chat(peer_uid, message)
					# 		# print reply
					# break

				# File Upload
				elif option == str(2):
					import cosnui
					import cosncontent
					path = cosnui.CosnUI.prompt_for_fname()
					if path is not None:
						# shared_link = peer.upload(path)
						shared_link = self.cloud.upload(path)
						entry = cosncontent.CosnContent.prompt()
						entry["time"] = "TODO"
						entry["item"] = shared_link
						cosncontent.CosnContent( self.storage.content_fname() ).insert(entry)
						# reupload updated content with its link in location file
						self.storage.create_location( self.server.address(), self.uid )
						print "Uploaded "  + path + " on " + shared_link
					else:
						print "No file selected. Canceling the upload."

				#
				# Initiate Friendship : send email with link to locatin.xml
				#
				elif option == str(3):
					peer_email = raw_input( "Enter your friend's email address: " )
					#
					# Check if the friend is online through location.xml
					#
					# If the friend is online,
					#	- save the friend's location.xml, ip address, port
					#	- Parse conent and download files referenced in content file
					#	
					# Else 
					#
					#
					url_to_location = self.friend_request(peer_email)
					print "Sent email to " + peer_email
					print "The location is " + url_to_location
				#
				# Confirm Friendship : connect to another peer on the socket shown on locatin.xml
				#
				elif option == str(4):
					url_to_location = raw_input("Enter the link to location of your friend: ")
					self.friend_request2(url_to_location)
				else:
					print "Please enter a number above."
				print

	# ------------------------------------------------------------------------
	# As Peer Client
	def _receive_from_peer(self, sock, stop="AtLineFeed"):
		message = ""
		char = ""
		sock.settimeout(10)	
		if stop == "AtLineFeed":
			while True:
				try:
					char = sock.recv(1)
				except:
					# print "sock.recv(1) timed out"
					return ""
				if char == "\n": 
					break
				else:
					message += char
			log_msg = self.uid + " received " + message
		elif stop == "1MB":
			message = sock.recv(1024*1024)
			log_msg = self.uid + " receiving a file."
		else:
			print "In _receive_from_peer(): Bug if this is shown."
		ActivityLog.Instance().log(log_msg)
		# if self.debug:
		# 	print "From Peer: ", message
		return message 

	def _send_to_peer(self, sock, message):
		if self.debug:
			log_msg = self.uid + " sent to   Peer: " + message
		ActivityLog.Instance().log(log_msg)
		sock.send(message + "\n")

	def init_tcp_conn(self,ip,port): 
		# TODO ip and port should be replaced by uid and the connection information should be cached
		sock = socket(AF_INET, SOCK_STREAM)
		sock.settimeout(2)           
		sock.connect((ip,int(port)))       
		return sock

	# TODO : peer to peer uid and retrieve from cache
	def address_of_peer(self, peer):
		location = self.udp_query( peer ) # TODO saori to saved peer
		words = location.split()
		ip = words[1]
		port = words[2]
		return ip,port

	def peer_chat(self, peer, message):
		# TODO : end-of-line => separate chat message
		# TODO : Show message sent on chat screen
		# location = self.udp_query( peer ) # TODO saori to saved peer
		# words = location.split()
		# ip = words[1]
		# port = words[2]
		# sock = self.init_tcp_conn(ip,port)
		# self.chat_screen.show_chat_message(message)
		print "In peer_chat peer = " + peer
		try:
			peer = self.peers[ peer ]
			sock = peer["sock"]
			peer["chat_counter"] += 1
			counter = peer["chat_counter"]
			self._send_to_peer(sock, "CHAT "+ str(counter) + " " + message)
			return self._receive_from_peer(sock)
		except KeyError:
			print "Trying to access " + peer + " but no such user in the list."
			return ""

	def peer_request(self, peer, profile_version):
		# This functio
		#	send REQUEST message, get profile updates for that, and parse posted files in <item> tags

		# Send REQUEST message
		ip,port = self.address_of_peer(peer)
		sock = self.init_tcp_conn(ip,port)
		self._send_to_peer(sock, "REQUEST " + str(profile_version) )

		# receive profile update and store it
		update = self._receive_from_peer(sock, "1MB" )
		xml = " ".join( update.split()[ 3: ] ) # TODO this changes indentation
		self.peer_profile = ET.fromstring( xml )

		# parse for posted files that are in <items> tags
		posted_items = []
		# print list(self.peer_profile)
		for ver in self.peer_profile.findall("version"): 
			item = ver.find("item")
			if item is not None:
				self.posted_files.append(item.text)

		return self.peer_profile, self.posted_files

		# TODO on PHASE2
		# update local peer profile on hard disk
		# peer_profile_file = peer+"-profile.xml" 
		# profile = Profile(peer_profile_file)
		# profile.extend( update )
		# print "peer_request after extend ", profile.tostring()
		# print "TODO in peer_request : flush"
		# profile.flush()

	def peer_profile(self, version_in_request, sock): 
		# Create xml file that consists of all the profiles since the version_in_request
		current_profile_version  = self.profile.current_version_number()
		profile_update = self.profile.versions_between(int(version_in_request), current_profile_version ).tostring()
		profile_update_length = str( len(profile_update) )
		message = self.uid + " " + str(current_profile_version) + " " +  str(profile_update_length) + " " + profile_update

		self._send_to_peer( sock, message )

	def peer_terminate(self):
		print "well, our program terminates connection for every message..."
	
	# ------------------------------------------------------------------------
	# Thread
	def stop(self):
		self.server_stop.set()

	# ------------------------------------------------------------------------

	def __init__(self, uid, email, passw=""):
		self.email = email
		self.chat_screen = ChatScreen()
		self.uid = uid
		self.gmail_pass = passw
		self.peers = {}

		# self.profile = Profile("profile.xml")
		# self.server = PeerServer()
		self.server = PeerWaiter(self)
		# self.server.set_client(self)

		# Cloud Part: Create and and publish location file on the cloud. Also
		# create profile and content if they do not exist.
		self.cloud = CosnDrop()
		self.storage = CosnStorage( self.cloud, self.uid )
		self.storage.create_location( self.server.address(), self.uid )

		# self.register_peer( self.uid, self.server.welcome_sock, self.storage.get_link_to_location()  )

	def register_peer(self, uid, sock, location_link):
		#	sock": tcp connection socket
		self.peers[uid] = { "sock":sock, "location":location_link, "chat_counter":0 }
		# print "id of self.peers on "+ self.uid
		print hex(id(self.peers))
		# print "Peer on "+self.uid, self.peers

	# ------------------------------------------------------------------------
	# friend request2 : make a friend request to the peer 1 who has sent the
	# email containing location of the peer1. 
	def friend_request2(self, peer_location):

		# Download files
		import tempfile 
		import cosnlocation
		import cosncontent

		#
		# Download http file in a variable
		#
		# TODO location dict and content array should be an object instead of
		# simple plain data struture since it's error prone
		#
		# Location
		peer_location = peer_location.replace('www.dropbox.com', 'dl.dropboxusercontent.com', 1) # TODO dropbox specific not here
		response = urllib2.urlopen(peer_location)
		location = cosnlocation.CosnLocation.parse( response.read() )
		#
		# Content
		content_link = location["content"]
		content_link = content_link.replace( 'www.dropbox.com', 'dl.dropboxusercontent.com', 1) # TODO dropbox specific not here
		content_xml = urllib2.urlopen(content_link).read()
		content = cosncontent.CosnContent.parse(content_xml)

		# Download all files referenced in the content file if it does not exist locally already
		self.download_from_wall(content, location["ID"] )

		# Start TCP connections to the peer for the chat, and 
		# Store that connectoin
		id = location["ID"]
		ip = location["IP"]
		port = port = location["port"]
		sock = self.init_tcp_conn(ip, port)

		print self.uid + "is trying connect to " + ip + " " + str(port)

		location_link = self.storage.get_link_to_location()

		message = "FRIEND "+self.uid + " " + location_link
		self._send_to_peer(sock, message) # TODO message
		self.register_peer(id, sock, peer_location)

		# Receive Friend Confirmation
		print self._receive_from_peer(sock)

		# TODO terminate all the connections on SIGINT

		# Public File TODO on Phase3?
		#
		# public_link  = location["public"]
		# response = urllib2.urlopen(public_link)
		# public = cosncontent.CosnPublic.parse( response.read() )
		# print public
		#

	def download_from_wall(self,content, prefix):
		#
		# Download all files referenced in the content file if not exist locally already
		#
		#	Just store everything with user ID of uploader as filename prefix
		#	in order to prevent file name collisions.
		#
		for entry in content:
			if "item" in entry:
				link = entry["item"]
				print link
				filename_postfix = os.path.basename(link)
				filename = prefix+"_"+filename_postfix
				if not os.path.exists(filename): 
					response = urllib2.urlopen(link)
					# print two new lines to not clutter the screen
					print ""
					print ""
					print "Downloading to " + filename
					f = open( filename, 'w'  )
					f.write(response.read())
					f.close

	# Send friend request through email (SMTP) that contains the link to
	# location.xml of this peer This one uses gmail.
	def friend_request(self, peer_email):
		#
		# [How to send email in Python via SMTPLIB](http://www.mkyong.com/python/how-do-send-email-in-python-via-smtplib/)
		#

		# 
		# debug print
		#
		# print "DEBUG PRINT IN friend_request"
		# print "self.email: ", self.email
		# print "peer_email", peer_email

		# link to location file
		url_to_location = self.storage.get_link_to_location()


		# handshake with gmail server
		smtpserver = SMTP("smtp.gmail.com",587)
		smtpserver.ehlo()
		smtpserver.starttls()
		smtpserver.ehlo()

		# gmail authentication
		if not self.gmail_pass:
			self.gmail_pass = getpass.getpass("Enter your gmail password: ")
		gmail_address = self.email
		smtpserver.login(gmail_address, self.gmail_pass)

		# Send the email through gmail server
		try:
			header = 'To:' + peer_email + '\n' + 'From: ' + gmail_address + '\n' + 'Subject: COSN Friend Request\n'
			msg = header + '\n '+ 'locatoin.xml: ' + url_to_location + ' \n\n'
			ActivityLog.Instance().log("Sent email about location file from " + gmail_address + " to " + peer_email )
			smtpserver.sendmail(gmail_address, peer_email, msg)
		except SMTPRecipientsRefused:
			# All recipients were refused. Nobody got the mail. The recipients attribute of the exception object is a dictionary with information about the refused recipients (like the one returned when at least one recipient was accepted).
			print "SMTPRecipientsRefused Error when sending friend request to " + peer_email
		except SMTPHeloError:
			# The server didn't reply properly to the HELO greeting.
			print "SMTPHeloError when sending friend request to " + peer_email
		except SMTPSenderRefused:
			# The server didn't accept the from_addr.
			print "SMTPSenderRefused Error when sending friend request to " + peer_email
		except SMTPDataError:
			# The server replied with an unexpected error code (other than a refusal of a recipient).
			print "SMTPData Error when sending friend request to " + peer_email
		# except: 
		# 	print "Unknown Error when sending friend request to " + peer_email
		

		# Closes Connection
		# TODO : difference of close() and quit()
		smtpserver.close()
		# smtpserver.quit()

		# return for debugging but this should be entered by the user receiving the email manually
		return url_to_location 
