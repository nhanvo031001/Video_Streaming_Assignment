from random import randint
import sys, traceback, threading, socket
import os
from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'
	SPEEDUP = 'SPEEDUP'
	SLOWDOWN = 'SLOWDOWN'
	DESCRIBE = 'DESCRIBE'
	SHOWSTAT = 'SHOWSTAT'
	FORWARD = 'FORWARD'
	BACKWARD = 'BACKWARD'
	EXIT = 'EXIT'
	SWITCH = 'SWITCH'

	FRAME_TO_FORWARD = 20
	FRAME_TO_BACKWARD = 20
	
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCHING = 3
	state = INIT

	

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	OK_200_DESCRIBE = 3		# for DESCRIBE button
	OK_200_SHOWSTAT = 4		# for STATISTIC button
	OK_200_SWITCH = 5
	
	clientInfo = {}
	
	def __init__(self, clientInfo):		
		self.clientInfo = clientInfo
		self.waitTime = 0	# for SPEEDUP, SLOWNDOWN
		
		# Create a dict to store data frame for forward:
		self.frameDict = {}
		self.clientInfo['currentPos'] =0 	# for DESCRIBE
		self.rtp_socket_opened = 0;
		self.frameSent = 0		# for Statistic button
		self.clientInfo['session'] = 0;
		self.client_exit = 0
		
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	def recvRtspRequest(self):
		"""Receive RTSP request from the client."""
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Data received:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
			if self.client_exit:
				connSocket.shutdown(socket.SHUT_RDWR)
				connSocket.close()
				print('\nEND THREAD FOR CLIENT\n')
				break
			
	
	def processRtspRequest(self, data):
		"""Process RTSP request sent from the client."""
		# Get the request type
		request = data.split('\n')
		line1 = request[0].split(' ')
		requestType = line1[0]
		
		# Get the media file name
		filename = line1[1]
		
		# Get the RTSP sequence number 
		seq = request[1].split(' ')
		
		# Process SETUP request
		if requestType == self.SETUP:
			if self.state == self.INIT:
				# Update state
				print("processing SETUP\n")
				
				try:
					print('Video:', filename)
					self.clientInfo['videoStream'] = VideoStream(filename)
					self.clientInfo['videoStream'].take_video_infomation()
					self.waitTime = 1/ self.clientInfo['videoStream'].frames_per_second
					self.state = self.READY
				except IOError:
					self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
				
				# Generate a randomized RTSP session ID
				if (self.clientInfo['session'] == 0):
					self.clientInfo['session'] = randint(100000, 999999)
				
				# Send RTSP reply
				self.replyRtsp(self.OK_200, seq[1])
				
				# Get the RTP/UDP port from the last line
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		# Process PLAY request 		
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("processing PLAY\n")
				self.state = self.PLAYING
				
				# Create a new socket for RTP/UDP
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				self.rtp_socket_opened = 1;
				self.replyRtsp(self.OK_200, seq[1])
				
				# Create a new thread and start sending RTP packets
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker']= threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		# Process PAUSE request
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("processing PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
			
				self.replyRtsp(self.OK_200, seq[1])
		
		# Process TEARDOWN request
		elif requestType == self.TEARDOWN:
			print("processing TEARDOWN\n")
			
			self.replyRtsp(self.OK_200, seq[1])
			self.state = self.INIT
			# Close the RTP socket
			if (self.rtp_socket_opened):
				self.clientInfo['rtpSocket'].shutdown(socket.SHUT_RDWR)
				self.clientInfo['rtpSocket'].close()
				self.rtp_socket_opened = 0
		
		# Process SPEEDUP request
		elif requestType == self.SPEEDUP:
			print("processing SPEEDUP\n")
			self.waitTime = self.waitTime / 2
			self.replyRtsp(self.OK_200, seq[1])
		
		# Process SLOWDOWN request
		elif requestType == self.SLOWDOWN:
			print("processing SLOWDOWN\n")
			self.waitTime = self.waitTime * 2
			self.replyRtsp(self.OK_200, seq[1])
		
		# Process DESCRIBE request
		elif requestType == self.DESCRIBE:
			print("processing DESCRIBE\n")
			self.replyRtsp(self.OK_200_DESCRIBE, seq[1])

		# process SHOWSTAT request
		elif requestType == self.SHOWSTAT:
			print("processing SHOWSTAT\n")
			self.replyRtsp(self.OK_200_SHOWSTAT, seq[1])

		# process FORWARD request
		elif requestType == self.FORWARD:
			print("processing FORWARD\n")
			# Set the number of frame to forward
			
			self.clientInfo['currentPos'] = min(self.clientInfo['currentPos'] + self.FRAME_TO_FORWARD, self.clientInfo['videoStream'].total_frames - self.clientInfo['videoStream'].frameNbr())
			
			self.replyRtsp(self.OK_200, seq[1])

		# process BACKWARD request
		elif requestType == self.BACKWARD:
			print("processing BACKWARD\n")
			# Set the number of frame backward
			self.clientInfo['currentPos'] = max(self.clientInfo['currentPos'] - self.FRAME_TO_BACKWARD, 0 - self.clientInfo['videoStream'].frameNbr())
			
			self.replyRtsp(self.OK_200, seq[1])
		elif requestType == self.SWITCH:
			print('processing SWITCH\n')
			self.state = self.SWITCHING
			self.replyRtsp(self.OK_200_SWITCH, seq[1])
		elif requestType == self.EXIT:
			self.client_exit = 1 # Khổng phản hồi cho client, chỉ end thread đang nghe rtsp từ client

			
	def sendRtp(self): #ABCDEF
		"""Send RTP packets over UDP."""
		while True:
			# Stop sending if request is PAUSE or TEARDOWN
			if self.clientInfo['event'].isSet():  #Pause thì end, không gởi nữa
				break 
			if self.rtp_socket_opened == 0: # đóng socket rồi (tức TEARDOWN) thì end, không gởi nữa
				break
			data = self.clientInfo['videoStream'].nextFrame() 
			if data or self.clientInfo['currentPos'] < 0: # Yêu cầu coi lại
				frameNumber = self.clientInfo['videoStream'].frameNbr() 
				# Store frame into clientInfo:
				self.frameDict[frameNumber] = data		# save each frame as an element of array frameDict
				try:
					address = self.clientInfo['rtspSocket'][1][0] 
					port = int(self.clientInfo['rtpPort'])
					#self.frameSent +=1
					#self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber),(address,port))
					if self.clientInfo['currentPos'] > 0:
						self.clientInfo['currentPos'] -= 1          # end - start + 1 ---> frame foward = 20 = end - start + 1 -----> -=1
					elif self.clientInfo['currentPos'] == 0:
						self.clientInfo['event'].wait(self.waitTime) 	# change for SPEEDUP
						self.frameSent += 1
						self.clientInfo['rtpSocket'].sendto(self.makeRtp(data, frameNumber), (address, port))
					else:
						# Gởi các frame backward
						pause = 0
						teardown = 0
						while self.clientInfo['currentPos'] < 0: # 
							if self.clientInfo['event'].isSet():  #Pause thì end, không gởi nữa
								pause = 1
								break 

							self.clientInfo['event'].wait(self.waitTime)
							frame_prior = frameNumber + self.clientInfo['currentPos']		# currentPos hien tai dang < 0
							data_prior = self.frameDict[frame_prior]		# lay video frame da luu trong array frameDict
							#print(f"currentPOS {self.clientInfo['currentPos']}")
							self.clientInfo['currentPos'] += 1
							self.frameSent += 1
							
							if self.clientInfo['event'].isSet():  #Pause thì end, không gởi nữa
								pause = 1
								break 
							self.clientInfo['rtpSocket'].sendto(self.makeRtp(data_prior, frame_prior), (address, port))
						# Gởi bù frame hiện tại đang chờ:
						if pause:
							break
						self.clientInfo['rtpSocket'].sendto(self.makeRtp(self.frameDict[frame_prior+ 1], frame_prior + 1), (address, port))
						self.frameSent +=1
						#print('Send backward:', frame_prior + 1)
				except:
					print("RTP sending failed!")
					#print('-'*60)
					#traceback.print_exc(file=sys.stdout)
					#print('-'*60)
			

	def makeRtp(self, payload, frameNbr):
		"""RTP-packetize the video data."""
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26 # MJPEG type
		seqnum = frameNbr
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	def replyRtsp(self, code, seq):
		"""Send RTSP reply to the client."""
		if code == self.OK_200:
			#print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())

		# Special case for DESCRIBE reply
		elif code == self.OK_200_DESCRIBE:
			info = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\n'
			#info += "===============================StreamInfo=========================\n"
			#info += "You are watching a video stream over UDP with RTP packetization\n"
			# Calculate the accurate frame_being_sent's Number
			#info += f"You have watched the video to frame: {self.clientInfo['videoStream'].frameNbr() + self.clientInfo['currentPos']}\n"
			# info += f"Video FPS: {self.clientInfo['videoStream'].frames_per_second}\n"
			#info += f"Total frames: {self.clientInfo['videoStream'].total_frames}\n"
			#info += f"Total duration: {self.clientInfo['videoStream'].total_duration}\n"
			#info += f"Video Encode: {self.clientInfo['videoStream'].video_encode}\n"
			#info += f"This message is sent over RTSP at: \n"
			#info += f"IP Address:{self.clientInfo['rtspSocket'][1][0]} | Port: {self.clientInfo['rtspSocket'][1][1]}\n"
			#info += f"This message is sent over utf8-encode\n"
			#info += "==================================================================\n"
			
			
			############ CLIENT SIDE RENDER cho dễ canh!!!!!
			info += "You are watching a video stream over UDP with RTP packetization\n"
			info += f"{self.clientInfo['videoStream'].height}\n"
			info += f"{self.clientInfo['videoStream'].width}\n"
			info += f"{self.clientInfo['videoStream'].frames_per_second}\n"
			info += f"{self.clientInfo['videoStream'].total_frames}\n"
			info += f"{self.clientInfo['videoStream'].total_duration}\n"
			info += f"{self.clientInfo['videoStream'].video_encode}\n"
			info += f"This message is sent over RTSP at: \n"
			info += f"{self.clientInfo['rtspSocket'][1][0]}\n"
			info += f"{self.clientInfo['rtspSocket'][1][1]}\n"
			info += f"This message is sent over utf8-encode\n"
			
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(info.encode())
		
		# Special case for SHOWSTAT reply
		elif code == self.OK_200_SHOWSTAT:
			info = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\n'
			info += f"Total Frames Sent: {self.frameSent}"
			print(f"Frames SENT: {self.frameSent}")
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(info.encode())
		# SWTICH reply
		elif code == self.OK_200_SWITCH:
			info = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\n'			
			file_list_string = self.find_all_videos()
			info += file_list_string
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(info.encode())
			self.state = self.INIT

		# Error messages
		elif code == self.FILE_NOT_FOUND_404:
			info = 'RTSP/1.0 404 NOT FOUND\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\n'	
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(info.encode())
			print("404 NOT FOUND")
		elif code == self.CON_ERR_500:
			info = 'RTSP/1.0 500 CONNECTION ERROR\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session']) + '\n'
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(info.encode())
			print("500 CONNECTION ERROR")
	
	def find_all_videos(self):
		file_list = ''
		for file_name in os.listdir():
			if file_name.endswith('Mjpeg'):
				file_list += (str(file_name) + '\n')
		return file_list
				
