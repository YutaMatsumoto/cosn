#!/usr/bin/env python

#
# Overview
#
# This class is used as a server that accept.  This class spawns threads so
# that an instance of this class can receive messages from multiple peers. 
#
#

from chatscreen import *
import cosnlocation
import cosncontent
import urllib2
from common import *
from cosn_log import *
from email.mime.text import MIMEText
from functools import wraps
from profile import *
from socket import *
import threading

#
# Waiter launches Servers 
#
#	Waiter has the one and only one welcoming socket, which spawns servers.
#	Each server is given a TCP connection socket created from the welcoming
#	socket of the Waiter.
#

lock = threading.Lock()
class PeerWaiter(threading.Thread):

	debug = True

	def address(self):
		# a little hackish way to get ip by accessing gmail server first
		# If it does not work, use gethostbyname(), which most likely returns
		# a loopback address on many linux distros.
		try:
			s = socket(AF_INET, SOCK_DGRAM)
			s.connect(("gmail.com",80))
			ip = s.getsockname()[0]
			s.close()
		except:
			ip = gethostbyname(gethostname())
			print "Exception Happend while trying to get IP address of the machine by creating a temporary socket." 
		port = self.welcome_port
		return { "ip":ip, "port":port }

	def __init__(self, client): 

		threading.Thread.__init__(self)
		self._stop = threading.Event()
		self.daemon = True

		PeerWaiter.client = client
		self.welcome_sock = socket(AF_INET,SOCK_STREAM) # TCP welcoming socket to serve peers
		self.welcome_port = get_open_port()
		self.welcome_sock.bind(('',self.welcome_port)) # SOMEDAY : port could not be open at this point. If so, retry.
		self.welcome_sock.listen(1)

		self.start()

	def __del__(self):
		# TODO : should be shutdown(SHUT_WR) ? close() does not collect resources immediately ?
		self.terminate()

	def terminate(self): 
		self.welcome_sock.close()	

	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def run(self):
		while True:
			if self.stopped():
				return
			else:
				self.welcome_sock.settimeout(3)
				try:
					sock, addr = self.welcome_sock.accept()

					lock.acquire()
					server = PeerServer( sock, self.client )
					lock.release()

					server.setDebug(2)
					# server.run()
				except timeout:
					# print "TIMEOUT IN WAITER"
					1

class PeerServer(threading.Thread):

	debug = True
	debugHeavy = True

	def setDebug(self, level=1):
		if level == 1:
			PeerServer.debug = True
		elif level >= 2:
			PeerServer.debugHeavy = True

	def __del__(self):
		# TODO : should be shutdown(SHUT_WR) ? close() does not collect resources immediately ?
		self.terminate()

	def terminate(self): 
		self.sock.close() # TODO do not close until terminate message
	
	def stop(self):
		self._stop.set()

	def stopped(self):
		return self._stop.isSet()

	def __init__(self, sock, client):

		# print lock
		lock.acquire()
		PeerServer.client = client
		lock.release()

		self.chat_screen = ChatScreen()

		threading.Thread.__init__(self)
		self._stop = threading.Event()
		self.daemon = True

		self.sock = sock
		self.start()

	def server_receive(self,sock):
		message = sock.recv(1024) # TODO buffer size
		if self.debug:
			lock.acquire()
			log_msg = self.client.uid + " received " + message
			lock.release()
		ActivityLog.Instance().log(log_msg)
		return message

	def server_send(self,sock,msg):
		sock.send(msg+"\n")
		1
		

	def serve_tcp_request(self):
		sock = self.sock
		try: 
			sock.settimeout(10) # TODO adjust TIMEOUT
			message   = self.server_receive(sock)
			words     = message.split()

			# if self.debugHeavy is True:
			print "SERVER : ", words

			if words[0] == "FRIEND":
				print "T FRIEND"
				# TODO separate CONFIRM as a function like tcp_pong
				peer_uid = words[1]
				peer_location_link = words[2]
				
				lock.acquire()
				print "Registering " + peer_uid + " on " + self.client.uid 
				self.client.register_peer(peer_uid, sock, peer_location_link )
				# self.client._send_to_peer(sock, "CONFIRM " + self.client.uid )
				self.server_send,(sock, "CONFIRM "+self.client.uid)
				lock.release()

				#
				# Get location and content from location
				#
				#	TODO create function for this for common usage
				response = urllib2.urlopen(peer_location_link)
				location = cosnlocation.CosnLocation.parse( response.read() )
				content_link = location["content"]
				content_link = content_link.replace( 'www.dropbox.com', 'dl.dropboxusercontent.com', 1) # TODO dropbox specific not here
				content_xml = urllib2.urlopen(content_link).read()
				content = cosncontent.CosnContent.parse(content_xml)

				lock.acquire()
				self.client.download_from_wall( content, peer_uid )
				lock.release()

				# print "FRIEND MESSAGE RECEIVED ON SERVER: ", words
			elif words[0] == "CHAT": 
				print "T CHAT"
				# TODO size limitation on message
				# chat = sock.recv(1024)
				counter = words[1]
				message = " ".join( words[2: ] ) # TODO HACK
				self.chat_screen.show_chat_message(message)
				# TODO separete delivered
				lock.acquire()
				self.client._send_to_peer(sock, "DELIVERED " + str(counter) )
				lock.release()
			else:
				print "T ELSE"
				print "Received insensible message: ", message

		except timeout:
			# print "Timeout in serve_tcp_request()"
			1

	def run(self):
		while 1:
			if self.stopped(): 
				return
			self.serve_tcp_request()
