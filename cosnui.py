import Tkinter, tkFileDialog

class CosnUI :


	def menu():
		1

	@staticmethod
	def prompt_for_fname():
		root = Tkinter.Tk()
		# file = tkFileDialog.askopenfile(parent=root,mode='rb',title='Choose a file to upload')
		filename = tkFileDialog.askopenfilename(parent=root,title='Choose a file to upload')
		if filename:
			return filename
		else: 
			return None

