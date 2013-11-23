#!/usr/bin/env python

from cosnui import *
from peer import *
import time

def early_exit():
	print "early exit."
	exit(1)


from subprocess import call
# Establish SIGINT handler for C-C quitting on terminal
def signal_handler(signal, frame):
	print "SIGINT received"
	# TODO
	# call(["kill", "python"])
	# peer.stop()
	sys.exit(1)

signal.signal(signal.SIGINT, signal_handler)

def test():

	u_email =  "utah.matsumoto@gmail.com"
	u = Peer("utah",u_email, "gooJ4o2j7O")
	m_email = "maybe_its_hot@msn.com"
	m = Peer("maybe", m_email )

	#
	# Test Friendship Initiation and Confmration
	#
	u_location = u.friend_request(m_email)
	m.friend_request2(u_location)

	# BUGBUF
	print "================= u's friends"
	print u.peers
	print "================= m's friends"
	print m.peers

	print "HELLO"

	#
	# Chat
	#
	m.peer_chat("utah", "HEY UTAH from Maybe")
	u.peer_chat("maybe", "Hey maybe from utah")
	



def main(email_address):
	# # TODO prompt for uid and email address
	# email_address = "utah.matsumoto@gmail.com"
	# uid = 'utahutahutah'
	# 
	# print email_address
	peer = Peer(uid, email_address)
	peer.ui()
	1

if __name__ == "__main__":

	path = sys.argv[1]
	uid = path
	print uid

	if path == "utah": 
		email_address = "utah.matsumoto@gmail.com"
		main(email_address)
	elif path == "maybe":
		email_address = "maybe_its_hot@msn.com"
		main(email_address)
	elif path == "saori":
		email_address = "isono22s@gmail.com"
		main(email_address)
	elif path == "bryam":
		email_address = "soccerbryam@gmail.com"
		main(email_address)
	elif path == "jikken":
		test()

	# Run Forever until Control-C
	while True:
		time.sleep( 60 )

