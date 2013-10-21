#!/usr/bin/env python

# From Ch2_application
from socket import *

# udp server
serverPort = 12000
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('', serverPort))
print "The server is ready to receive"
while 1:
	message, clientAddress = serverSocket.recvfrom(2048)
	print "Received Message from Client : " + message
	modifiedMessage = message.upper()
	serverSocket.sendto(modifiedMessage, clientAddress)

# tcp server?
# serverPort=12000
# serverSocket=socket(AF_INET, SOCK_STREAM)
# serverSocket.bind(('', serverPort))
# serverSocket.listen(1)
# print('The server is readly to receive')
# while 1:
# 	connectionSocket, addr= serverSocket.accept()
# 	sentence=connectionSocket.recv(1024)
# 	capSentence = sentence.upper()
# 	connectionSocket.send(capSentence)
# 	connectionSocket.close()
