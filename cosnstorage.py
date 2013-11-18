# This class defines logic to create/update/store/retrieves files used by
# COSN. This class exists so that COSN can work with multiple cloud storage
# provider such as dropbox/google-drive/skydrive. This class as an argument of
# __init__ rereives a cloud-storage-class instance, which does basic cloud
# file io. The cloud-storage-class must implement the following python
# methods. 
#
#	download(filename)
#		donwload the file with the filename and return it in a string variable
#
#	upload(filename)
#		upload the file with the filename to the cloud storage.
#
#	fileexists(filename)
#		check if the file with the filename exists and return True/False
#
class CosnStorage:
	def __init__(storage):
		1
