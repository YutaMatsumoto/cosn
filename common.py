import sys

def get_open_port():
	# From [get open TCP port in Python - Stack Overflow](http://stackoverflow.com/questions/2838244/get-open-tcp-port-in-python)
	import socket
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind(("",0))
	s.listen(1)
	port = s.getsockname()[1]
	s.close()
	return port


