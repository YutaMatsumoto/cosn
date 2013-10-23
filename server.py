#!/usr/bin/env python

import pprint
import signal
import sys
from socket import *

#
# functions
#

# TODO : Thread ? 
def ping(uid,ip,port):
	print "PINGing " + uid + " " + ip + " " + str(port)
	message = "PING " + uid + " " + ip + " " + str(port)
	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((ip,int(port)))
	sock.send(message)
	# TODO : timeout = 60 seconds
	sock.settimeout(1)
	# TODO : check pong message
	success = True
	try: 
		pong = sock.recv(1024)
		print "From Client : ", pong
	except timeout: 
		success = False
	sock.close()
	return success


# release resources on sigint
def signal_handler(signal, frame):
	print "SIGINT received"
	sys.exit(0)
	sock.close()
signal.signal(signal.SIGINT, signal_handler)

# command line parameter
sys.argv.pop(0)
for arg in sys.argv: 
	if 0 < len( sys.argv ):
		port = int( sys.argv[0] )
		print "binding port: " + sys.argv[0]
	else:
		print "Usage : server.py portnumber "
		sys.argv.pop(0)
		sys.exit(1)

# udp server parameters
print "server listining on port : ", port
sock = socket(AF_INET, SOCK_DGRAM)
sock.bind(('', port))
bufsize=2048

# client info variables
ctable = {} 


# Handle Client Request
while 1:
	message, caddr = sock.recvfrom(bufsize)
	print "From Client of "+str(caddr)+ ": " + message
	words = message.split()
	if len(words)<1: 
		print "wrong client request"
		sys.exit(2)
	if words[0] == "REGISTER":
		if len(words)<4: 
			print "Number of arguments for REGISTER command is not enough."
			sys.exit(3)
		cmuid=words[1]  # client message uid
		cmaddr=words[2] # client message address
		cmport=words[3] # client message port
		ctable[cmuid] = { "address":cmaddr, "port":cmport } # cmport is welcoming tcp socket of client
		# Sending ACK
		print "Sending ACK Message to Client Desitined To ", caddr, "From ", 
		ackmsg = "ACK " + cmuid + " " + ctable[cmuid]["address"] + " " + ctable[cmuid]["port"]
		# print "Client Address: ", caddr
		sock.sendto(ackmsg,caddr) # This is not received by client
		pprint.pprint(ctable)
	elif words[0] == "QUERY": 
		if len(words)<2:
			print "Number of arguments for QUERY command is not enough"
			sys.exit(4)
		uid = words[1]
		if uid in ctable:
			address = ctable[uid]['address']
			port = ctable[uid]['port']
		else:
			address = '0.0.0.0'
			port = "0"
		sock.sendto( "LOCATION " + address + " " + port, caddr)
	elif words[0] == "QUIT":
		uid_in_message = words[1]
		ip_in_message = words[2]
		ip_source = caddr[0]
		if ip_in_message != ip_source:
			print "\tSUSPICIOUS: IP address in message and the source IP address are different."
			print "caddr, ip_in_message", ip_source, ip_in_message
		else:
			ctable.pop(uid_in_message)
	elif words[0] == "DOWN":
		uid = words[1]
		ip = words[2]
		port = words[3]
		ponged = ping(uid, ip, port)
		if not ponged: 
			try:
				del ctable[uid]
			except KeyError:
				1
	else:
		print "msg type : "+ words[0]
	
