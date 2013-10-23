#!/usr/bin/env python

import signal
import sys
from socket import *


# From [get open TCP port in Python - Stack Overflow](http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python)
def get_open_port():
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(("",0))
	s.listen(1)
	port = s.getsockname()[1]
	s.close()
	return port

def parse_command():
	if 3 > len( sys.argv ):
		print "usage : client.py user-id server-ip server-port"
		print "argv: ", sys.argv
		sys.exit(1)
	sys.argv.pop(0); 
	uid   = sys.argv[0] ; sys.argv.pop(0)
	sip = sys.argv[0] ; sys.argv.pop(0)
	sport = int( sys.argv[0] )
	saddr = (sip, sport)
	return uid, saddr


class Client: 

	uid = -1                             # username
	saddr = ()                           # address (ip,port) to register on the server
	pssock = socket(AF_INET,SOCK_STREAM) # tcp socket to serve peers
	psport = -1                          # port pssock binds to
	csock = socket(AF_INET, SOCK_DGRAM)  # udp socket to connect to server

	def __init__(self, uid, saddr): 
		self.uid = uid
		self.saddr = saddr
		self.setup_peer_server()

	def __del__(self):
		self.pssock.close()	
		self.csock.close()
		# pssock.shutdown(SHUT_WR) # TODO
	def setup_peer_server(self):
		# Establish Peer Server (ps) for Peer Client (pc)
		# TODO need to pick open port
		# TODO this blocks at accept()
		self.psport = get_open_port()
		# pssock =  socket(AF_INET,SOCK_STREAM)
		self.pssock.bind(('',self.psport))
		self.pssock.listen(1)
		# see p108 of Ch2 ppt
		# pconn, paddr = pssock.accept() # connection socket with new peer
		# sentence = pconn.recv(1024)
		# pconn.close()
		# pssock.close()
		return self.pssock, self.psport

	def udp_register(self,uid,ip):
		# TODO arg not needed since they are member variables
		trycount = 0
		while trycount < 3:
			# TODO use _send_to_central_server()
			header = "REGISTER " 
			body = uid + " " + ip + " " + str(self.psport)
			message = header + body
			self.csock.sendto(message,saddr)
			# TODO confirm ACK body match up with local uid,address,port
			self.csock.settimeout(1)  # timeout for ACK receipt is 10 sec TODO timeout is set to 1 when devloping
			try: 
				smsg,aaaa = self.csock.recvfrom(2048) # Receive ACK
			except timeout:
				trycount+=1
				continue
			break

	def udp_query(self, uid): 
		self._send_to_central_server("QUERY "+uid)
		self.csock.settimeout(1)
		# TODO parses message and return
		try: 
			smsg,aaaa = self.csock.recvfrom(2048) # Receive LOCATION
			print smsg
			return smsg
		except timeout:
			print "TIMEOUT on QUERY"

	def udp_quit(self):
		ip = self.saddr[0]
		port = str(self.saddr[1])
		self._send_to_central_server("QUIT " + self.uid + " " + ip + " " + port )

	def udp_down(self, uid, ip, port):
		self._send_to_central_server( "DOWN " + uid + " " + ip + " " + port )

	def tcp_pong(self,sock):
		# Note: gethostname() doesn't always return the fully qualified domain name; use getfqdn() (see above).
		# TODO choose csock or pssock or something else
		hostname = gethostbyname(gethostname())
		sock.send("PONG " + self.uid + " " + hostname + " " + str(self.psport) )

	def _send_to_central_server(self, message):
		self.csock.sendto(message, saddr)

	def start_chat(self,peer_ip):
		print "impl start_chat()"
		1

	def process_tcp_request(self):
		# self.csock.settimeout(2)
		# try: 
		# 	message,address=self.csock.recvfrom(2048)
		# 	words = message.split()
		# 	print "WORDS: ", words
		# except timeout:
		# 	print "csock timeout in process_tcp_request()"
		# 	1
		sock,addr = self.pssock.accept()
		sock.settimeout(3) # TODO adjust TIMEOUT
		try: 
			message   = sock.recv(2048)
			words     = message.split()
			print "Received ", message
			if words[0] == "PING": 
				# TODO check PING parameters
				self.tcp_pong(sock)
			elif words[0] == "FRIEND":
				# TODO separate CONFIRM as a function like tcp_pong
				peer_uid = words[1]
				sock.send( "CONFIRM " + self.uid )
				self.start_chat( peer_ip )

			sock.close()
		except timeout:
			print "pssock timeout in process_tcp_request()"
			1

	def peer_friend(self, peer_id):
		location = self.udp_query( peer_id )
		uid,ip,port= location.split()
		if ip == "0.0.0.0" and port == 0: 
			print "The user does not exit."
			return False
		else: 
			message = "FRIEND " + uid
			sock = socket(AF_INET, SOCK_STREAM)
			sock.settimeout(1) # TODO increase TIMEOUT
			try: 
				print "ip and port of the peer: ", ip,port
				sock.connect((ip,port)) # TODO TODO TODO TODO TODO TODO
				sock.send(message)
				print "after sock.send(message) in peer_friend"
				confirmation = sock.recv(1024)
				# TODO : check confirmation content
			except:
				self.udp_down(uid,ip,port)
		


# if __name__ = "__main__":
uid, saddr = parse_command()
u = Client(uid,saddr)
u.udp_register(uid, "127.0.0.1")
if u.uid == "saori":
	1	
elif u.uid == "ymat" or u.uid == "yuta":
	u.peer_friend("saori")
else:
	print "uid not yuta/ymat nor soari"
# u.udp_query(uid)
# u.udp_quit()
# u.udp_query(uid)
# u.udp_down(uid, "127.0.0.1", str(u.psport) )
# u.peer_friend("saori")
while 1: 
	u.process_tcp_request()
