#!/usr/bin/env python

from cosn_log import *
import pprint
import signal
import sys
from socket import *
import xml.etree.ElementTree as ET


# ------------------------------------------------------------------------------
# Program Conguration

def signal_handler(signal, frame):
	# release resources on sigint
	print "SIGINT received"
	sys.exit(0)
	sock.close()
signal.signal(signal.SIGINT, signal_handler)

def parse_command(): 
	sys.argv.pop(0)
	if 0 < len( sys.argv ):
		port = int( sys.argv[0] )
		print "binding port: " + sys.argv[0]
		return port
	else:
		print "Usage : server.py portnumber "
		print "Example : $ ./server.py 12121"
		return None

# udp server parameters
def setup_udp_socket(port):
	print "server listining on port : ", port
	sock = socket(AF_INET, SOCK_DGRAM)
	sock.bind(('', port))
	return sock



# ------------------------------------------------------------------------------
# Server Functions

# This prints client table.
def print_ctable():
	# TODO pretty print
	pprint.pprint(ctable)

# SOMEDAY : Thread / select ? 
def ping(uid,ip,port):
	print "PINGing " + uid + " " + ip + " " + str(port)
	message = "PING " + uid + " " + ip + " " + str(port)
	sock = socket(AF_INET, SOCK_STREAM)
	sock.connect((ip,int(port)))
	sock.send(message)
	sock.settimeout(60)
	# TODO : check pong message
	success = True
	try: 
		pong = sock.recv(1024)
		print "From Client : ", pong
	except timeout: 
		success = False
	sock.close()
	return success



# ------------------------------------------------------------------------------
# Main

port = parse_command()
if port is None:
	sys.exit(1)
sock_bufsize = 2048
sock = setup_udp_socket(port)
ctable = {} # client info variables

# Handle Client Request
while 1:
	message, caddr = sock.recvfrom(sock_bufsize)
	log_msg = "Central Server received from Client of "+str(caddr)+ ": " + message
	ActivityLog.Instance().log(log_msg)
	words = message.split()
	if len(words)<1: 
		print "wrong client request"
		sys.exit(2)
	if words[0] == "REGISTER":
		if len(words)<4: 
			errlog = "Number of arguments for REGISTER command is not enough: " + " ".join(words)
			ErrorLog.Instance.log(errlog)
			continue
			# sys.exit(3)
		cmuid=words[1]  # client message uid
		cmaddr=words[2] # client message address
		cmport=words[3] # client message port
		ctable[cmuid] = { "address":cmaddr, "port":cmport } # cmport is welcoming tcp socket of client
		# send ACK
		ackmsg = "ACK " + cmuid + " " + ctable[cmuid]["address"] + " " + ctable[cmuid]["port"]
		sock.sendto(ackmsg,caddr) # This is not received by client
	elif words[0] == "QUERY": 
		if len(words)<2:
			errlog = "Number of arguments for QUERY command is not enough: " + " ".join(words)
			ErrorLog.Instance.log(errlog)
			continue
		uid = words[1]
		if uid in ctable:
			address = ctable[uid]['address']
			port = ctable[uid]['port']
		else:
			address = '0.0.0.0'
			port = "0"
		sock.sendto( "LOCATION " + address + " " + port, caddr)
	elif words[0] == "QUIT":
		if len(words) < 3
			errlog = "Number of arguments for QUIT is not enough: " + ( " ".join(words) )
			ErrorLog.Instance.log(errlog)
			continue
		uid_in_message = words[1]
		ip_in_message = words[2]
		ip_source = caddr[0]
		if ip_in_message != ip_source:
			print "\tSUSPICIOUS: IP address in message and the source IP address are different."
			print "caddr, ip_in_message", ip_source, ip_in_message
		else:
			ctable.pop(uid_in_message)
	elif words[0] == "DOWN":
		if len(words) < 4
			errlog = "Number of arguments for DOWN is not enough: " + ( " ".join(words) )
			ErrorLog.Instance.log(errlog)
			continue
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
	
