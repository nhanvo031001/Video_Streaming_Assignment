import sys
from tkinter import Tk
from Client import Client
from config_client import DEFAULT_SERVER_ADDRESS, DEFAULT_SERVER_PORT, DEFAULT_RTP_PORT, FILE_NAME
if __name__ == "__main__":
	try:
		serverAddr = DEFAULT_SERVER_ADDRESS
		serverPort = DEFAULT_SERVER_PORT
		rtpPort = DEFAULT_RTP_PORT
		fileName = FILE_NAME
	except Exception as error:
		print("CLIENT INITIALIZATION FAILED\n")	
	
	root = Tk()
	
	# Create a new client
	# Calling client from Client.py
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()

	