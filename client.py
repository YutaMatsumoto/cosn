#!/usr/bin/env python

#
# Overview
#
# This program acts as a client program of COSN specified on
# <http://www.cse.unr.edu/~mgunes/cpe400/project1.htm>. This client has
# capability to access the central server to query the information regarding
# the peers, initiate communication with other peers, and serve other peers. 
#
# This file consists of Client class and some code to create one client and
# run that client. Each message defined in the specification earns a method in
# the client and named likewise (Ex. QUERY message is named udp_query() ).
#

#
# Usage 
#
# The usage will be given by a help option on the program. Invoke the program
# with -h or --help.
#

#
# Variable Name Convension
#
#	ps : peer server     : server that serves requests of the peers. I.e., this client.
#	cs : central server  : server that handles udp requests of clients.
#

# Client Method Name Convension
#
#	"udp" is used as a prefix for methods that send  requests to the central server
#	"peer" is used as a preifx for methods that send requests to peer servers.
#

	
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

# ------------------------------------------------------------------------------
# Client
class Client(threading.Thread):

	debug = True

	# About This Client, which servs as a peer server (ps) as well.
	uid = -1 # user ID of this client, registered on the central server
	chatting = False
	chat_screen = ChatScreen()
	profile = None

	# Peer Connection Variables
	chat_counter = 0
	peer_profile = None # Element
	posted_files = []

	# Peer Server Variales
	ps_sock = socket(AF_INET,SOCK_STREAM) # TCP welcoming socket to serve peers
	ps_port = -1                          # port number the TCP socket above binds to 

	# Central Server Variables
	cs_ip = -1   # IP address of central server
	cs_port = -1 # port number of central server for UDP requests
	cs_sock = socket(AF_INET, SOCK_DGRAM) # udp socket to connect to server

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def __init__(self, uid, cs_ip, cs_port, role):

		# super(Client, self).__init__()
		threading.Thread.__init__(self)
		self._stop = threading.Event()

		self.cs_ip, self.cs_port = cs_ip, cs_port
		self.chat_screen = ChatScreen()
		self.uid = uid
		self.role = role
		if self.role == "client":
			1
		elif self.role == "server":
			1
			self.profile = Profile("profile.xml")
			self.ps_port = get_open_port()
			self.ps_sock.bind(('',self.ps_port))
			self.ps_sock.listen(1)
			self.udp_register()
		else:
			print "unknown role: ", self.role

	def terminate(self): 
			self.ps_sock.close()	
			self.cs_sock.close()

	def __del__(self):
		# TODO : should be shutdown(SHUT_WR) ? close() does not collect resources immediately ?
		self.terminate()

	def udp_register(self):
		trycount = 0
		while trycount < 3:
			header = "REGISTER " 
			body = self.uid + " " + self.cs_ip + " " + str(self.ps_port)
			self._send_to_central_server( header + body )
			self.cs_sock.settimeout(1)  # timeout for ACK receipt is 10 sec TODO timeout is set to 1 when devloping
			try: 
				ack_msg,address = self._receive_from_central_server()  # Receive ACK
				# TODO confirm ACK body matches up with local uid,address,port
			except timeout:
				trycount+=1
				continue
			break

	def udp_query(self, uid): 
		self._send_to_central_server("QUERY "+uid)
		self.cs_sock.settimeout(1)
		# TODO parse message and return it
		try: 
			location, address = self._receive_from_central_server() # Receive LOCATION
			return location
		except timeout:
			print "Timeout on QUERY-ing ", uid

	def udp_quit(self):
		ip = self.cs_ip
		port = str(self.cs_port)
		self._send_to_central_server("QUIT " + self.uid + " " + ip + " " + port )

	def udp_down(self, uid, ip, port):
		self._send_to_central_server( "DOWN " + uid + " " + ip + " " + port )

	# -----------------------------------------------------------------------

	def tcp_pong(self,sock):
		# Note: gethostname() doesn't always return the fully qualified domain name; use getfqdn() (see above).
		hostname = gethostbyname(gethostname())
		self._send_to_central_server( "PONG " + self.uid + " " + hostname + " " + str(self.ps_port) ) 
		# sock.send("PONG " + self.uid + " " + hostname + " " + str(self.ps_port) )

	# ------------------------------------------------------------------------

	def cs_address(self): 
		return (self.cs_ip, self.cs_port)

	# ------------------------------------------------------------------------
	
	def _send_to_central_server(self, message):
		if self.debug: 
			log_msg = self.uid + " sent to CentralServer: " + message
		ActivityLog.Instance().log(log_msg)	
		self.cs_sock.sendto( message + "\n" , self.cs_address() )

	def _receive_from_central_server(self):
		# TODO buffer size
		(message, address) = self.cs_sock.recvfrom(2048)
		if (self.debug):
			log_msg = self.uid + " received from CentralServer: " + message
			ActivityLog.Instance().log(log_msg)
		return message, address

	# ------------------------------------------------------------------------
	# As Peer Server 
	
	def server_receive(self,sock):
		message = sock.recv(1024) # TODO buffer size
		if self.debug:
			log_msg = self.uid + " received " + message
		ActivityLog.Instance().log(log_msg)
		return message

	def serve_tcp_request(self):
		try: 
			sock,addr = self.ps_sock.accept()
			sock.settimeout(3) # TODO adjust TIMEOUT
			message   = self.server_receive(sock)
			words     = message.split()

			if words[0] == "PING": 
				# TODO check PING parameters
				self.tcp_pong(sock)
			elif words[0] == "FRIEND":
				# TODO separate CONFIRM as a function like tcp_pong
				peer_uid = words[1]
				if self.chatting == False:
					self.chatting = True
					self._send_to_peer(sock, "CONFIRM " + self.uid )
				else:
					sock.send( "BUSY " + self.uid )
			elif words[0] == "CHAT": 
				if self.chatting == True:
					# TODO size limitation on message
					# chat = sock.recv(1024)
					counter = words[1]
					message = words[2]
					self.chat_screen.show_chat_message(message)
					# TODO separete delivered
					self._send_to_peer(sock, "DELIVERED " + str(counter) )
				else: 
					if self.debug:
						print "Ignoring CHAT message since FRIEND message has not been received."
			elif words[0] == "REQUEST": 
				version = words[1]
				self.peer_profile(version, sock)
			elif words[0] == "RELAY": 
				# TODO PHASE2 : check if this client has any information about the uid on the RELAY message
				# and return 
				uid = words[1]
				version = words[2]
				self.peer_profile(version, sock)
			elif words[0] == "GET":
				filename = words[1]
				self.peer_file(filename, sock)
			else:
				print "Received insensible message: ", message
			sock.close() # TODO do not close until terminate message

		except timeout:
			print "Timeout in serve_tcp_request()"

	# ------------------------------------------------------------------------
	# As Peer Client
	
	def _receive_from_peer(self, sock, stop="AtLineFeed"):
		message = ""
		char = ""
		if stop == "AtLineFeed":
			while True:
				char = sock.recv(1)
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

	def address_of_peer(self, peer):
		location = self.udp_query( peer ) # TODO saori to saved peer
		words = location.split()
		ip = words[1]
		port = words[2]
		return ip,port

	def peer_friend(self, peer_id):
		location = self.udp_query( peer_id )
		uid,ip,port= location.split()
		if ip == "0.0.0.0" and port == 0: 
			print "The user does not exit."
			return False
		else: 
			message = "FRIEND " + uid
			try: 
				sock = self.init_tcp_conn(ip,port)
				self._send_to_peer(sock, message)
				# TODO : check confirmation content
				confirmation = self._receive_from_peer(sock)
			except timeout:
				print self.uid, "failed friend request"
				self.udp_down(uid,ip,port)
				confirmation = ""
			return confirmation
		
	def peer_chat(self, peer, message):
		# TODO : end-of-line => separate chat message
		# TODO : Show message sent on chat screen
		location = self.udp_query( peer ) # TODO saori to saved peer
		words = location.split()
		ip = words[1]
		port = words[2]
		sock = self.init_tcp_conn(ip,port)
		self.chat_screen.show_chat_message(message)
		self.chat_counter += 1
		self._send_to_peer(sock, "CHAT "+ str(self.chat_counter) + " " + message)
		return self._receive_from_peer(sock)

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

	def peer_relay(self,peer,profile_version):
		ip,port = self.address_of_peer(peer)
		sock = self.init_tcp_conn(ip,port)
		self._send_to_peer(sock, "RELAY " + peer + " " + str(profile_version) )

	def peer_profile(self, version_in_request, sock): 
		# Create xml file that consists of all the profiles since the version_in_request
		current_profile_version  = self.profile.current_version_number()
		profile_update = self.profile.versions_between(int(version_in_request), current_profile_version ).tostring()
		profile_update_length = str( len(profile_update) )
		message = self.uid + " " + str(current_profile_version) + " " +  str(profile_update_length) + " " + profile_update

		self._send_to_peer( sock, message )

	def peer_get(self, peer, filename):
		# TODO if file already exists locally outside of this function
		if self.posted_files is None: 
			print "No post files have been obtained yet."
		else:
			# Send Request
			location = self.udp_query(peer)
			ip = location.split()[1]
			port = location.split()[2]
			sock = self.init_tcp_conn(ip,port)
			message = "GET " + filename
			self._send_to_peer(sock, message)

			# Receive File
			reply = self._receive_from_peer(sock, "1MB")
			filename = "from_"+peer+"_"+os.path.basename(filename)
			file = open(filename, 'wr')

			# throw away first three words
			reply = reply.partition(' ')[2]
			reply = reply.partition(' ')[2]
			reply = reply.partition(' ')[2]
			file.write(reply)
			file.close()
			print "file saved to " + filename
			# print file.read()

	def peer_file(self, filename, sock):
		fileexists = os.path.exists(filename)
		if fileexists:
			f = open(filename, 'r')	
			filestr = f.read()
			filesize= len(filestr)
			message = "FILE " + filename + " " + str(filesize) + " " + filestr
			log_msg = self.uid + " sent a file, "+filename
		else:
			message = "FILE " + filename + " " + str(0)
			log_msg = self.uid + " cannot send a file since the file, "+filename+" does not exist."
		ActivityLog.Instance().log(log_msg)
		sock.send(message)
		# self._send_to_peer(sock, message)

	def peer_terminate(self):
		print "well, our program terminates connection for every message..."

	# ------------------------------------------------------------------------
	# Thread
	def run(self):

		# As Server
		if self.role == "server":
			while 1:
				self.serve_tcp_request()
			print "client being run as server"

		# As Client
		elif self.role == "client":
			while True:
				if self.stopped():
					return
				# Prompt for peer to connect to and get the ip and port of tcp socket of the peer.
				while True:
					peer_uid = raw_input( "Enter who you want to communicate with: " )
					location = self.udp_query(peer_uid)
					ip = location.split()[1]
					port = location.split()[2]
					if ip == "0.0.0.0" and port == "0":
						print "The user, "+peer_uid+ ", is not registered on the central server."
						continue
					else:
						break
				# Prompt for what to do
				while True:
					print "What would you like to do?"
					print "1. Chat"
					print "2. File Download"
					option = raw_input( "Please enter number > " )

					# Do CHAT
					if option == str(1):
						reply = self.peer_friend(peer_uid)	
						reply = reply.split()[0] 
						# reply_peer = reply.split()[1] 
						if reply == "CONFIRM":
							while True:	
								message = raw_input("Enter Message to Send > ")
								reply = self.peer_chat(peer_uid, message)
								print reply
						elif reply == "BUSY":
							print peer_uid + " is busy."
							# print reply_peer + " is busy."
						break

					# Do File Download by REQUEST and GET
					elif option == str(2):
						profile, posted_files = self.peer_request(peer_uid,1)	
						for i in range(0,len(posted_files)):
							print str(i+1) + ". " + posted_files[i]
						file_number = raw_input("Enter number for the file to download > ") 
						index = int(file_number) - 1
						file_to_get = posted_files[index]
						self.peer_get(peer_uid, file_to_get)
						break

					else:
						print "Please enter 1 or 2."


# ------------------------------------------------------------------------------
# Test

def udp_tests(): 
	# parse_command consumes ?
	uid, cs_ip, cs_port = parse_command()
	u = Client(uid,cs_ip,cs_port)
	# ------------------------------------------------------------------------------
	# Tests : UDP requests
	#
	u.udp_query(uid)
	u.udp_quit()
	u.udp_query(uid)
	u.udp_down(uid, "127.0.0.1", str(u.ps_port) )
	if uid != "saori":
		u.peer_friend("saori")

def tcp_tests():
	# parse_command consumes ?
	uid, cs_ip, cs_port = parse_command()
	u = Client(uid,cs_ip,cs_port)
	# ------------------------------------------------------------------------------
	# Tests : TCP requests
	#
	#	saori is server
	#	ymat is client
	#
	# u.udp_register(uid, "127.0.0.1")
	if u.uid == "saori":
		while 1: 
			u.serve_tcp_request()
	elif u.uid == "ymat" or u.uid == "yuta":
		u.peer_friend("saori")
		u.peer_chat("saori", "Waaatup!!!")	
		u.peer_request("saori", 2)
		u.peer_get("saori", "profile.xml")
		u.peer_terminate()
		# u.peer_relay("saori", 1)
	else:
		print "uid not yuta/ymat nor soari"

# ------------------------------------------------------------------------------

def print_usage():
	print "usage : client.py user-id server-ip server-port"
	print "argv: ", sys.argv


def parse_command():
	if 3 >= len( sys.argv ):
		print_usage()
		sys.exit(1)
	sys.argv.pop(0); 
	uid   = sys.argv[0] ; sys.argv.pop(0)
	cs_ip = sys.argv[0] ; sys.argv.pop(0)
	try: 
		cs_port = int( sys.argv[0] )
	except ValueError:
		print_usage()
		print "port number must number. but <"+sys.argv[0]+"> is given."
		sys.exit(1)
		
	print "uid, server ip, server port = ", uid, cs_ip, cs_port
	return uid, cs_ip, cs_port


# ------------------------------------------------------------------------------
# Main

# profile = Profile( "profile.xml" )
# print profile.tostring()

from subprocess import call
# Establish SIGINT handler for C-C quitting on terminal
def signal_handler(signal, frame):
	print "SIGINT received"
	# TODO
	# call(["kill", "python"])
	client_client.stop()	
	sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)

if __name__ == "__main__":

	# parse information for central server(cs) information on command line
	uid, cs_ip, cs_port = parse_command()
	client_client = Client(uid,cs_ip,cs_port, "client")
	client_server = Client(uid,cs_ip,cs_port, "server")
	client_client.daemon = True
	client_server.daemon = True
	client_client.start()
	client_server.start()

	# TODO thread join	
	# client_client.join()	
	# client_server.join()

	# Client("")

	# [Python Programming/Threading - Wikibooks, open books for an open world](http://en.wikibooks.org/wiki/Python_Programming/Threading)
	# clientclient = 
	# clientserver =
