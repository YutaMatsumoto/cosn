#!/usr/bin/env python

#
# Overview
#
# This program acts as a client program of COSN specified on
# <http://www.cse.unr.edu/~mgunes/cpe400/project1.htm>. This client has
# capability to access the central server to query the information regarding
# the peers, and initiate communication with other peers, and serve other peers. 
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

from profile import *
import errno
import os
import signal
import sys
from socket import *

# ------------------------------------------------------------------------------
# Util
def get_open_port():
	# From [get open TCP port in Python - Stack Overflow](http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python)
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(("",0))
	s.listen(1)
	port = s.getsockname()[1]
	s.close()
	return port

def parse_command():
	if 3 > len( sys.argv ):
		print "usage : client.py user-id server-ip [server-port]"
		print "argv: ", sys.argv
		sys.exit(1)
	sys.argv.pop(0); 
	uid   = sys.argv[0] ; sys.argv.pop(0)
	cs_ip = sys.argv[0] ; sys.argv.pop(0)
	cs_port = int( sys.argv[0] )
	print "uid, server ip, server port = ", uid, cs_ip, cs_port
	return uid, cs_ip, cs_port

# ------------------------------------------------------------------------------
# ChatScreen TODO
class ChatScreen: 
	def __init__(self):
		1
	def show_chat_message(self, message): 
		print "ChatScreen: ", message

# ------------------------------------------------------------------------------
# Client
class Client: 

	debug = True

	# About This Client, which servs as a peer server (ps) as well.
	uid = -1 # user ID of this client, registered on the central server
	chatting = False
	chat_screen = ChatScreen()
	profile = None

	# Peer Connection Variables
	chat_counter = 0

	# Peer Server Variales
	ps_sock = socket(AF_INET,SOCK_STREAM) # TCP welcoming socket to serve peers
	ps_port = -1                          # port number the TCP socket above binds to 

	# Central Server Variables
	cs_ip = -1   # IP address of central server
	cs_port = -1 # port number of central server for UDP requests
	cs_sock = socket(AF_INET, SOCK_DGRAM) # udp socket to connect to server

	def __init__(self, uid, cs_ip, cs_port): 
		self.chat_screen = ChatScreen()
		self.uid = uid
		self.cs_ip, self.cs_port = cs_ip, cs_port
		self.ps_port = get_open_port()
		self.ps_sock.bind(('',self.ps_port))
		self.ps_sock.listen(1)
		self.udp_register()
		self.profile = Profile("profile.xml")

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
		# TODO choose cs_sock or ps_sock or something else
		hostname = gethostbyname(gethostname())
		sock.send("PONG " + self.uid + " " + hostname + " " + str(self.ps_port) )

	# ------------------------------------------------------------------------

	def cs_address(self): 
		return (self.cs_ip, self.cs_port)

	# ------------------------------------------------------------------------
	def _send_to_central_server(self, message):
		if self.debug: 
			print "To   Central Server: ", message
		self.cs_sock.sendto( message, self.cs_address() )

	def _receive_from_central_server(self):
		# TODO buffer size
		(message, address) = self.cs_sock.recvfrom(2048)
		if (self.debug):
			print "From Central Server: ", message
		return message, address

	# ------------------------------------------------------------------------
	# As Peer Server 
	
	def serve_tcp_request(self):
		try: 
			sock,addr = self.ps_sock.accept()
			sock.settimeout(3) # TODO adjust TIMEOUT
			message   = sock.recv(1024)
			words     = message.split()

			if self.debug: 
				print "Received ", message

			if words[0] == "PING": 
				# TODO check PING parameters
				self.tcp_pong(sock)
			elif words[0] == "FRIEND":
				# TODO separate CONFIRM as a function like tcp_pong
				peer_uid = words[1]
				if self.chatting == False:
					self.chatting = True
					sock.send( "CONFIRM " + self.uid )
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
			elif words[0] == "RELAY": # TODO
				uid = words[1]
				version = words[2]
				self.peer_profile(version, sock)
			else:
				print "Received insensible message: ", message
			sock.close() # TODO do not close until terminate message

		except timeout:
			print "Timeout in serve_tcp_request()"

	# ------------------------------------------------------------------------
	# As Peer
	
	def _receive_from_peer(self, sock): 
		message = sock.recv(1024)
		if self.debug:
			print "From Peer: ", message
		return message 

	def _send_to_peer(self, sock, message):
		if self.debug:
			print "To   Peer: ", message
		sock.send(message)

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
		self._receive_from_peer(sock)

	def peer_request(self, peer, profile_version):

		# Send REQUEST message
		ip,port = self.address_of_peer(peer)
		sock = self.init_tcp_conn(ip,port)
		self._send_to_peer(sock, "REQUEST " + str(profile_version) )

		# receive profile update for new versions
		update = self._receive_from_peer(sock)

		# TODO on phase2
		# update local peer profile on hard disk
		# peer_profile_file = peer+"-profile.xml" 
		# profile = Profile(peer_profile_file)
		# profile.extend( update )
		# print "peer_request after extend ", profile.tostring()
		# print "TODO in peer_request : flush"
		# profile.flush()


	def peer_profile(self, version_in_request, sock): 
		# note file_length is sent as an ascii string
		# TODO indicate current version
		# Create xml file that consists of all the profiles since the version_in_request
		current_profile_version  = self.profile.current_version_number()
		profile_update = self.profile.versions_between(int(version_in_request)+1, current_profile_version ).tostring()
		profile_update_length = str( len(profile_update) )
		message = self.uid + " " + str(current_profile_version) + " " +  str(profile_update_length) + " " + profile_update

		self._send_to_peer( sock, message )
		


# ------------------------------------------------------------------------------
# Tests : UDP requests
#
# u.udp_query(uid)
# u.udp_quit()
# u.udp_query(uid)
# u.udp_down(uid, "127.0.0.1", str(u.ps_port) )
# u.peer_friend("saori")
#

# ------------------------------------------------------------------------------
# Main

# profile = Profile( "profile.xml" )
# print profile.tostring()

def signal_handler(signal, frame):
	print "SIGINT received"
	client.terminate()
	sys.exit(1)
signal.signal(signal.SIGINT, signal_handler)

# if __name__ = "__main__":
uid, cs_ip, cs_port = parse_command()
u = Client(uid,cs_ip,cs_port)

# u.udp_register(uid, "127.0.0.1")
if u.uid == "saori":
	while 1: 
		u.serve_tcp_request()
elif u.uid == "ymat" or u.uid == "yuta":
	u.peer_friend("saori")
	u.peer_chat("saori", "Waaatup!!!")	
	u.peer_request("saori", 2)
	# u.peer_request("saori", 2)
else:
	print "uid not yuta/ymat nor soari"
