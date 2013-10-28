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
