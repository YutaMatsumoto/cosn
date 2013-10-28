default:
	@x-terminal-emulator -e ./server.py 10013 & 
	@./client.py saori 127.0.0.1 10013
	@./client.py ymat  127.0.0.1 10013
	@pkill python

clean: 
	mv tags *.pyc /tmp
