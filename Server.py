import sys, socket
from config_server import DEFAULT_SERVER_PORT
from ServerWorker import ServerWorker

class Server:	
	
	def main(self):
		try:
			SERVER_PORT = DEFAULT_SERVER_PORT
		except:
			print("[Usage: Server.py Server_port]\n")
		rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		rtspSocket.bind(('', SERVER_PORT))
		rtspSocket.listen(5)        

		# Receive client info (address,port) through RTSP/TCP session
		while True:
			clientInfo = {}
			clientInfo['rtspSocket'] = rtspSocket.accept()
			# socket.accept() return: connection_socket, client_address
			ServerWorker(clientInfo).run()		

if __name__ == "__main__":
	(Server()).main()


