import sys
from tkinter import Tk
from Client import Client
from config_client import FILE_NAME	#comment
if __name__ == "__main__":
	try:
		serverAddr = sys.argv[1]
		serverPort = sys.argv[2]
		rtpPort = sys.argv[3]	#rtp port
		fileName = FILE_NAME
	except Exception as error:
		print("CLIENT INITIALIZATION FAILED\n")	
		print("[Usage: ClientLauncher.py Server_name Server_port RTP_port]\n")	
	
	root = Tk()
	
	# Create a new client
	# Calling client from Client.py
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")	
	root.mainloop()
	