from tkinter import *
import tkinter.font as font
import tkinter.messagebox
from PIL import Image, ImageTk
import socket, threading, sys, os
from datetime import datetime
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

lock = threading.Lock()
def debug_message(mssg):
	print ('\nDEBUG MESSAGE: ' + str(mssg) + '\n')
class Client:
	# State
	INIT = 0
	READY = 1
	PLAYING = 2
	SWITCHING = 3
	state = INIT


	FRAME_TO_BACKWARD = 20

	# Button
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3

	# More buttons
	DESCRIBE = 4  
	SHOWSTAT = 5 
	SPEEDUP = 6
	SLOWDOWN = 7
	FORWARD = 8
	BACKWARD = 9
	SWITCH = 10
	EXIT = 11
	# Initiation..
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master        # master is GUI
		self.master.resizable(False, False) 
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()        # UI
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		# Sequence Number
		self.rtspSeq = 0
		self.sessionId = 0
		# Check if a TEARDOWN message is received
		self.requestSent = -1
		self.teardownAcked = 0
		# Connect to server to send RTSP messages
		self.connectToServer()
		self.frameNbr = 0
		# Variable to calculate session statistics (SHOWSTAT):
		self.count = 0
		self.sizeData = 0
		self.curSecond = 0
		self.curSeqNum = 0
		self.frameServerSent = 0
		self.receivedTotalFrameNum = FALSE      # # when receiving reply from server ---> will show statistic
		#self.sendRtspRequest(self.SETUP)       # for setup automatically
		#self.setupMovie()
		self.start_pause_state = 'start'
		self.waiting_to_quit = 0
		self.safe_to_setup = 1
		self.streaminfo_hide = 1
		self.done_switch = 1

		self.receive_rtsp_reply_thread = threading.Thread(target=self.recvRtspReply, daemon=True)
		self.receive_rtsp_reply_thread.start()
	def createWidgets(self):
		"""Build GUI."""

		# Create a label to display the movie
		self.label = Label(self.master, height=20)
		self.label.grid(row=0, column=0, columnspan=6, sticky=W + E + N + S, padx=5, pady=5)

		myFont = font.Font(weight="bold")       # bold text

		# Create Setup button
		setup_image = PhotoImage(file = r"./assets/icons8-setting-32.png")
		setup_image = setup_image.subsample(1, 1)
		self.setup = Button(self.master,width =150 ,compound = LEFT, padx=3, pady=3, bg='#09aeae', image=setup_image)
		self.setup.image = setup_image 
		self.setup["text"] = "Setup"
		self.setup["font"] = myFont
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=1, padx=2, pady=2,sticky=N + S + E + W)

		# Create Play Pause button
		play_image = PhotoImage(file = r"./assets/play-button.png")
		play_image = play_image.subsample(1, 1)
		self.play_pause_button = Button(self.master,width = 150, compound = LEFT, padx=3, pady=3, bg='#09aeae', image=play_image)
		self.play_pause_button.image = play_image
		self.play_pause_button["text"] = "Play"
		self.play_pause_button["font"] = myFont
		self.play_pause_button["command"] = self.handle_play_pause_button
		self.play_pause_button.grid(row=1, column=2, padx=2, pady=2,sticky=N + S + E + W)


		# Create Teardown button
		teardown_image = PhotoImage(file = r"./assets/icons8-stop-32.png")
		teardown_image = teardown_image.subsample(1, 1)
		self.teardown = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image= teardown_image)
		self.teardown.image = teardown_image
		self.teardown["text"] = "Teardown"
		self.teardown["font"] = myFont
		self.teardown["command"] = self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2,sticky=N + S + E + W)

		# Create SLOWDOWN button
		slowdown_image = PhotoImage(file = r"./assets/slowdown.png")
		slowdown_image = slowdown_image.subsample(1, 1)
		self.slowdown = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image=slowdown_image)
		self.slowdown.image = slowdown_image
		self.slowdown["text"] = "Slow Down"
		self.slowdown["font"] = myFont
		self.slowdown["command"] = self.decreaseSpeed
		self.slowdown.grid(row=2, column=0, padx=2, pady=2,sticky=N + S + E + W)

		# Create SPEEDUP button
		speedup_image = PhotoImage(file = r"./assets/speedup.png")
		speedup_image = speedup_image.subsample(1, 1)
		self.speedup = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image=speedup_image)
		self.speedup.image = speedup_image
		self.speedup["text"] = "Speed Up"
		self.speedup["font"] = myFont
		self.speedup["command"] = self.increaseSpeed
		self.speedup.grid(row=2, column=1, padx=2, pady=2,sticky=N + S + E + W)

		# Create BACKWARD button
		backward_image = PhotoImage(file = r"./assets/bward.png")
		backward_image = backward_image.subsample(1, 1)
		self.backward = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image=backward_image)
		self.backward.image = backward_image
		self.backward["text"] = "Backward"
		self.backward["font"] = myFont
		self.backward["command"] = self.backwardVideo
		self.backward.grid(row=2, column=2, padx=2, pady=2,sticky=N + S + E + W)

		# Create FORWARD button
		forward_image = PhotoImage(file = r"./assets/fward.png")
		forward_image = forward_image.subsample(1, 1)
		self.forward = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image=forward_image)
		self.forward.image = forward_image
		self.forward["text"] = "Forward"
		self.forward["font"] = myFont
		self.forward["command"] = self.forwardVideo
		self.forward.grid(row=2, column=3, padx=2, pady=2,sticky=N + S + E + W)

		# Create SWITCH button
		switch_image = PhotoImage(file = r"./assets/switch.png")
		switch_image = switch_image.subsample(1, 1)
		self.switch = Button(self.master,width =150 , compound = LEFT, padx=3, pady=3, bg='#09aeae', image=switch_image)
		self.switch.image = switch_image
		self.switch["text"] = "Switch"
		self.switch["font"] = myFont
		self.switch["command"] = self.handle_switch_button
		self.switch.grid(row=1, column=0, padx=2, pady=2,sticky=N + S + E + W)


		# Draw horizontal line:       # Row increase 1 because MORE BUTTONS in below row
		self.horizontal1 = Text(self.master, width=30, height=2, bg='#70baff')
		self.horizontal1.grid(row=4, columnspan=4, sticky=E + W)

		# Create Label for stream info:
		self.infoLabel = Label(self.master, width=15, text="VIDEO STATISTIC", font='bold')
		self.infoLabel.grid(row=5, column=0, padx=4, pady=2)

		# Create DESCRIBE button
		describe_image = PhotoImage(file = r"./assets/clear.png")
		describe_image = describe_image.subsample(1, 1)
		self.describe = Button(self.master,width =150 , compound=LEFT, padx=3, pady=3, bg='#09aeae', image=describe_image)
		self.describe.image = describe_image
		self.describe["text"] = "Clear"
		self.describe["font"] = myFont
		self.describe["command"] = self.handle_clear_button
		self.describe.grid(row=5, column=1, padx=2, pady=2,sticky=N + S + E + W)
	   
	   
	   
		# Create CLEAR BUTTON button
		describe_image = PhotoImage(file = r"./assets/search.png")
		describe_image = describe_image.subsample(1, 1)
		self.describe = Button(self.master,width =150 , compound=LEFT, padx=3, pady=3, bg='#09aeae', image=describe_image)
		self.describe.image = describe_image
		self.describe["text"] = "Describe"
		self.describe["font"] = myFont
		self.describe["command"] = self.displayInfo
		self.describe.grid(row=5, column=2, padx=2, pady=2,sticky=N + S + E + W)



		#Create SHOWSTAT button
		showstat_image = PhotoImage(file = r"./assets/graph.png")
		showstat_image = showstat_image.subsample(1, 1)
		self.showStat = Button(self.master,width =150 , compound=LEFT, padx=3, pady=3, bg='#09aeae', image=showstat_image)
		self.showStat.image = showstat_image
		self.showStat["text"] = "Statistic"
		self.showStat["font"] = myFont
		self.showStat["command"] = self.displayStat
		self.showStat.grid(row=5, column=3, padx=2, pady=2,sticky=N + S + E + W)


		# Create TextArea to display stream infomation:
		self.streaminfo = Text(self.master, height=13, width=30)
		self.streaminfo.configure(font=("Courier", 13))
		self.streaminfo.configure(state='disabled')
		self.streaminfo.grid_forget();
		
	def handle_clear_button(self):
		self.streaminfo.configure(state='normal')
		self.streaminfo.delete(1.0,END)
		self.streaminfo.configure(state='disabled')
		self.streaminfo.grid_forget()
		self.streaminfo_hide = 1

	def setupMovie(self):
		"""Setup button handler."""
		if self.state == self.INIT and self.safe_to_setup:     # state is INIT --> allow set up
			self.safe_to_setup = 0
			self.sendRtspRequest(self.SETUP)    # send request to set up movie
			

	def exitClient(self):
		"""Teardown button handler."""
		if self.state != self.INIT and self.state != self.SWITCHING:
			self.sendRtspRequest(self.TEARDOWN)     # send request to close
			
	def convert_play_to_pause(self):
		self.start_pause_state = 'pause'
		pause_image = PhotoImage(file = r"./assets/icons8-pause-32.png")
		pause_image = pause_image.subsample(1, 1)
		self.play_pause_button["image"] = pause_image
		self.play_pause_button.image = pause_image
		self.play_pause_button["text"] = "Pause"
	def convert_pause_to_play(self):
		play_image = PhotoImage(file = r"./assets/play-button.png")
		play_image = play_image.subsample(1, 1)
		self.start_pause_state = 'start'
		self.play_pause_button.image = play_image
		self.play_pause_button["image"] = play_image
		self.play_pause_button["text"] = "Play"
	def handle_play_pause_button(self):
		if self.state == self.SWITCHING:
			return
		if self.start_pause_state == 'start':
			self.playMovie()
		else:
			self.pauseMovie()

	
	def pauseMovie(self):
		"""Pause button handler."""
		if self.state == self.PLAYING:      # state is playing --> allow pause
			self.sendRtspRequest(self.PAUSE)

	def playMovie(self):
		"""Play button handler."""  
		
		if self.state == self.INIT:
			lock.acquire() # Đưa lock về 0 trước, sẵn sàng khoá thread này nếu aquire lần nữa
			# Đặt lock đầu ở trước khi gởi request để nếu reply có về trước lock thứ 2 thì cũng sẽ không bị deadlock
			# do release chỉ cho phép chạy khi đã lock ít nhất  1 lần --> Cần xét đã lock tránh lỗi 
			# --> Khi reply sớm hơn lock --> lock.release thì sẽ bỏ qua không nhả--> deadlock
			self.setupMovie() # Setup - Gởi yêu cầu - Tạo thread nhận reply
			debug_message('BLOCK THE MAIN THREAD, WAITING FOR SETUP REPLY')
			lock.acquire() # Khoá thread này lại - Thread nhận reply sẽ mở khoá cho nó - Không chạy tiếp nếu chưa thấy reply về
			lock.release() # Trả khoá về như mặc định (1) sau khi đã được mở khoá
			
		if self.state == self.READY:        # state is ready --> allow play
			# Create a new thread to listen for RTP packets
			debug_message('START RTP PACKET RECEIVER THREAD')
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()  # Event(): quan ly flag, set() flag true, clear() flag false, wait() block until flag true
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)
		
	
	def increaseSpeed(self):
		"""Speedup button handler"""
		if self.state != self.INIT:
			self.sendRtspRequest(self.SPEEDUP)

	def decreaseSpeed(self):
		"""Slowdown button handler"""
		if self.state != self.INIT:
			self.sendRtspRequest(self.SLOWDOWN)

	def forwardVideo(self):
		if self.state != self.INIT:
			self.sendRtspRequest(self.FORWARD)

	def backwardVideo(self):
		if self.state != self.INIT:
			self.sendRtspRequest(self.BACKWARD)

	def displayInfo(self):      # for describe button
		"""Describe button handler"""
		if self.state != self.INIT:
			self.sendRtspRequest(self.DESCRIBE)
	
	def displayStat(self):
		"""Show Stat button handler"""
		if self.state != self.INIT:
			self.sendRtspRequest(self.SHOWSTAT)
			while True:
				if self.receivedTotalFrameNum:
					break
			if (self.streaminfo_hide):
				self.streaminfo.grid(row=6, column=0, columnspan=4, sticky=W + E + N + S, padx=2, pady=2)
				self.streaminfo_hide = 0
				
			stat_to_show = "============================STATISTIC=============================\n"
			# stat_to_show += f"Current Seq Num:{self.curSeqNum} \t \t StreamDuration:{self.curSecond}\n"
			stat_to_show += f"Current Seq Num:{self.curSeqNum} \t \n"
			stat_to_show += f"Received Frame Count: {self.count} \t \n"
			stat_to_show += f"Total Frame Server Sent: {self.frameServerSent}\n"
			
			if self.frameServerSent > 0:
				stat_to_show += f"Packet Loss Rate: {1 - (self.count / self.frameServerSent)}\n"
			else:
				stat_to_show += f"Packet Loss Rate: oo (Server has sent 0 frame)\n"
			stat_to_show += f"Ratio: {self.sizeData / self.curSecond} bytes per second\n"
			stat_to_show += "==================================================================\n\n\n"
			self.streaminfo.configure(state='normal')
			self.streaminfo.insert(END, stat_to_show)
			self.streaminfo.configure(state='disabled')
			# Remove the FLAG for next time
			self.receivedTotalFrameNum = FALSE

	def listenRtp(self):
		"""Listen for RTP packets."""
		# Get time before receiving the packet
		
		# mới bỏ
		before = datetime.now()         # for caculate bytes/seconds (ratio)
		
		while True:
			try:
				data = self.rtpSocket.recv(20480)       # receive rtp packet from server
				# Keep track of the number of data frames received
				self.count = self.count + 1     # count for frames received, for statistic
				if data:
					
					
					# 

					
					# Depacket the RtpPacket, in RtpPacket.py
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					# Get the current time after receiving the packet in hour : minute : second format
					currentTime = datetime.now()
					# Parse the string and convert the time interval to seconds
				   
				   
				   
					# curResult = str(currentTime - before).split(':')        # curResult[0] hour, curResult[1] minute, curResult[2] second  
					# self.curSecond += float(curResult[0]) * 3600 + float(
					#     curResult[1]) * 60 + float(curResult[2])


					# chỉnh lại cách tính curSecond
					curResult = str(currentTime - before).split(':')
					before = currentTime
					self.curSecond += float(curResult[0]) * 3600 + float(
						curResult[1]) * 60 + float(curResult[2])



					self.sizeData = self.sizeData + sys.getsizeof(data) # for statistic, ratio

					currFrameNbr = rtpPacket.seqNum()       # frame video received from server
										
					print("Current Sequence Number: " + str(currFrameNbr))

					self.curSeqNum = rtpPacket.seqNum()
					if currFrameNbr > self.frameNbr:  # Discard the late packet
						self.frameNbr = currFrameNbr
					# Dont tab this line in, or else it will create auto skip when backward
					self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Stop listening upon requesting PAUSE or TEARDOWN
				if self.playEvent.isSet():
					break
				# Upon receiving ACK for TEARDOWN request,
				# close the RTP socket
				if self.teardownAcked == 1:
					break
		debug_message('END RTP PACKET RECEIVER THREAD')
	def writeFrame(self, data):     # return image file, then updateMovie function use to show on GUI
		"""Write the received frame to a temp image file. Return the image file."""
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")    # writing binary format
		file.write(data)
		file.close()

		return cachename

	def updateMovie(self, imageFile):   # show image as video on GUI
		"""Update the image file as video frame in the GUI."""
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image=photo, width=photo.width(), height=photo.height())
		self.label.image = photo

	def connectToServer(self):
		"""Connect to the Server. Start a new RTSP/TCP session."""
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		debug_message('CREATE RTSP SOCKET')
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkinter.messagebox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

	def sendRtspRequest(self, requestCode):
		"""Send RTSP request to the server."""
		# -------------
		# TO COMPLETE
		# -------------
		# Setup request
		if requestCode == self.SETUP and self.state == self.INIT:
			debug_message('START RTSP REPLY RECEIVER THREAD')
			# Update RTSP sequence number.
			self.rtspSeq = self.rtspSeq + 1
			# Write the RTSP request to be sent.
			request = f"SETUP {self.fileName} RTSP/1.0\n"   #fileName = name of file video
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Transport: RTP/UDP; client_port= {self.rtpPort}"
			# Keep track of the sent request.
			# self.requestSent = ...
			self.requestSent = self.SETUP

		# Play request
		elif requestCode == self.PLAY and self.state == self.READY:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = f"PLAY {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"    # order of rtsp packet sent
			request += f"Session: {self.sessionId}"
			# Keep track of the sent request.
			self.requestSent = self.PLAY

		# Pause request
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Update RTSP sequence number.
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			request = f"PAUSE {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			# Keep track of the sent request.
			self.requestSent = self.PAUSE

		# Teardown request
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Update RTSP sequence number.
			# ...
			self.rtspSeq += 1
			# Write the RTSP request to be sent.
			# request = ...
			request = f"TEARDOWN {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			# Keep track of the sent request.
			# self.requestSent = ...
			self.frameNbr = 0
			self.requestSent = self.TEARDOWN

		# SPEEDUP request
		elif requestCode == self.SPEEDUP and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"SPEEDUP {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.SPEEDUP

		# SLOWDOWN request
		elif requestCode == self.SLOWDOWN and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"SLOWDOWN {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.SLOWDOWN

		# DESCRIBE request
		elif requestCode == self.DESCRIBE and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"DESCRIBE {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.DESCRIBE

		# Connect to server to receive the total frame sent by server
		elif requestCode == self.SHOWSTAT and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"SHOWSTAT {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.SHOWSTAT

		elif requestCode == self.FORWARD and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"FORWARD {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.FORWARD

		elif requestCode == self.BACKWARD and (self.state == self.READY or self.state == self.PLAYING):
			self.rtspSeq += 1
			request = f"BACKWARD {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.frameNbr -= self.FRAME_TO_BACKWARD
			self.requestSent = self.BACKWARD
		elif requestCode == self.SWITCH and self.state == self.SWITCHING:
			self.rtspSeq += 1
			request = f"SWITCH {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.SWITCH
		elif requestCode == self.EXIT:
			self.rtspSeq += 1
			request = f"EXIT {self.fileName} RTSP/1.0\n"
			request += f"Cseq: {self.rtspSeq}\n"
			request += f"Session: {self.sessionId}"
			self.requestSent = self.EXIT
		else:
			return

		# Send the RTSP request using rtspSocket.
		self.rtspSocket.sendall(request.encode("utf-8"))
		print('\nData sent:\n' + request)   # print request above

	def recvRtspReply(self):
		"""Receive RTSP reply from the server."""
		while True:
			# Không treo socket nếu đã teardown, chỉ spin lock chờ (data rỗng sẽ treo socket nếu không set timeout)
			if self.safe_to_setup: #Spin liên tục để không nhận reply, trừ khi yêu cầu switch hoặc tắt app
				if self.waiting_to_quit: # Yêu cầu tắt app
					break
				elif self.state == self.SWITCHING: # Nếu 
					pass
				else:
					continue 
			reply = self.rtspSocket.recv(1024)  # reveive reply from server

			if reply:
				self.parseRtspReply(reply.decode("utf-8"))

			if self.requestSent == self.TEARDOWN:
				try:
					os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Delete the cache image from video
				except:
					debug_message('NO CACHED TO DELETE')
				self.rtpSocket.shutdown(socket.SHUT_RDWR)
				self.rtpSocket.close()
				debug_message('CLOSE RTP SOCKET')
				# Kiểm tra nếu main thread (đang chạy giao diện) đang waiting để quit thì set giao diện lại sẽ gây lỗi
				if self.waiting_to_quit: 
					break
				play_image = PhotoImage(file = r"./assets/play-button.png")
				play_image = play_image.subsample(1, 1)
				self.start_pause_state = 'start'
				self.play_pause_button.image = play_image
				self.play_pause_button["image"] = play_image
				self.play_pause_button["text"] = "Play"
				self.safe_to_setup = 1;

		debug_message('END RTSP REPLY RECEIVER THREAD')

	def parseRtspReply(self, data):     # get session id and sequence number of video
		"""Parse the RTSP reply from the server."""
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		# Process only if the server reply's sequence number is the same as the request's
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# New RTSP session ID
			if self.sessionId == 0:
				self.sessionId = session

			# Process only if the session ID is the same
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200:      # status code la 200 OK --> nhan reply thanh cong
					if self.requestSent == self.SETUP:
						# Update RTSP state.
						self.state = self.READY
						self.teardownAcked = 0
						# Open RTP port.
						self.openRtpPort()                  # de nhan data video frame server gui\
						
						# Nhả khoá, mở khoá thread đang đợi ở play button
						if (lock.locked()):
							debug_message('RECEIVED SETUP REPLY, RELEASE LOCK')
							lock.release() # Mở khoá main thread đang chờ


					elif self.requestSent == self.PLAY:
						# update state
						self.state = self.PLAYING   
						self.convert_play_to_pause()

					elif self.requestSent == self.PAUSE:
						# update state
						self.state = self.READY
						# The play thread exits. A new thread is created on resume.
						self.playEvent.set()
						self.convert_pause_to_play()
					
					elif self.requestSent == self.TEARDOWN:
						# update state
						self.state = self.INIT
						# Flag the teardownAcked to close the socket.
						self.teardownAcked = 1
						self.curSecond = 0      # new, myself
						self.sizeData = 0	# new,myself

						if (lock.locked()):
							debug_message('RECEIVED TEARDOWN REPLY, RELEASE LOCK')
							lock.release() # Mở khoá main thread đang chờ
						

					elif self.requestSent == self.DESCRIBE:
						if (self.streaminfo_hide):
							self.streaminfo.grid(row=6, column=0, columnspan=4, sticky=W + E + N + S, padx=2, pady=2)
							self.streaminfo_hide = 0
						print("Client parsing DESCRIBE")
						
						print(lines)
						self.total_frame = lines[7]
						self.total_duration = lines[8]

						#print("total frame: ", self.total_frame)
						#print("total duration: ", self.total_duration)

						# print("CURRENT POSITION VIDEO: ", int(self.frameNbr) / int(self.total_frame) * int(float(self.total_duration)))
						# print("TIME REMAINING: ", int(float(self.total_duration)) - (int(self.frameNbr) / int(self.total_frame) * int(float(self.total_duration))) )
						
						current_position_video = str( int(self.frameNbr) / int(self.total_frame) * int(float(self.total_duration)) )
						time_remaining = str( int(float(self.total_duration)) - (int(self.frameNbr) / int(self.total_frame) * int(float(self.total_duration))) )

						stream_infomation = "==========================STREAM INFOMATION=======================\n"
						stream_infomation += "You have watched video to frame: " + str(self.frameNbr) + '\n'
						stream_infomation += lines[3] + '\n'
						stream_infomation += "Video height: " + lines[4] + '\n'
						stream_infomation += "Video width: " + lines[5] + '\n'
						stream_infomation += "Video defaut FPS: " + lines[6] + '\n'
						stream_infomation += "Video total frames: " + lines[7] + '\n'
						stream_infomation += "Video total duration: " + lines[8] + '\n'
						stream_infomation += "Video encode: " + lines[9] + '\n'
						stream_infomation += lines[10] + '\n'
						stream_infomation += "IP Address: " + lines[11] + " | Port: " + lines[12] + '\n'
						stream_infomation += lines[13] + '\n'
						stream_infomation += "Current position: " + str(current_position_video) + '\n'
						stream_infomation += "Remaining time: " + str(time_remaining) + '\n'
						stream_infomation += "==================================================================\n\n\n"
						self.streaminfo.configure(state='normal')
						self.streaminfo.insert(END, stream_infomation)
						self.streaminfo.configure(state='disabled')

					elif self.requestSent == self.SHOWSTAT:
						self.frameServerSent = int(lines[3].split(':')[1].strip())
						self.receivedTotalFrameNum = True
					
					elif self.requestSent == self.SWITCH:
						self.file_list = lines[3:]
						self.file_list.pop(); # phần empty
						if len(self.file_list) == 0:
							tkinter.messagebox.showwarning(title= "Warning", message= "Server does not have any Video!")
						else:
							self.done_switch = 0
							self.select_window = Toplevel(self.master)
							self.select_window.resizable(False, False) 
							self.select_window.protocol("WM_DELETE_WINDOW", lambda: self.close_select_menu(self.select_window))
							self.select_variable = StringVar()
							self.select_variable.set(self.fileName)
							self.choose_menu = OptionMenu(self.select_window, self.select_variable, *self.file_list)
							myFont = font.Font(weight="bold") 
							self.choose_menu["font"] = myFont
							self.choose_menu.grid(row = 0, column=0, sticky=N+S+E+W)
							self.select_button = Button(self.select_window, width = 15 , compound=LEFT, padx=3, pady=3, bg='#09aeae');
							self.select_button["text"] = "Select"
							self.select_button["font"] = myFont
							self.select_button["command"] = self.select_video
							self.select_button.grid(row=1, column=0, padx=2, pady=2,sticky=N + S + E + W)
							self.state = self.INIT
				else:
					print('ERROR, SERVER REPLY:', lines[0])
	def select_video(self):
		self.fileName = self.select_variable.get()
		self.select_window.destroy()
		self.done_switch = 1
	def close_select_menu(self, select_window):
		select_window.destroy()
		self.done_switch = 1
	def openRtpPort(self):
		"""Open RTP socket binded to a specified port."""
		# -------------
		# TO COMPLETE
		# -------------
		# Create a new datagram socket to receive RTP packets from the server
		# self.rtpSocket = ...
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		debug_message('CREATE RTP SOCKET')
		# Set the timeout value of the socket to 0.5sec
		# ...
		self.rtpSocket.settimeout(0.5)

		try:
			# Bind the socket to the address using the RTP port given by the client user
			# ...
			self.state = self.READY
			self.rtpSocket.bind(('', self.rtpPort))     # rtpPort: la port nhan video frame
		except:
			tkinter.messagebox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

	
	def handle_switch_button(self):
		if self.state == self.SWITCHING: # Tránh spam khi đang chờ reply
			return
		if self.done_switch == 0: # Đang mở 1 cửa sổ switch
			return
		if self.state != self.INIT:
			lock.acquire() # Đưa lock về 0 trước, sẵn sàng khoá thread này nếu aquire lần nữa
			# Đặt lock đầu ở trước khi gởi request để nếu reply có về trước lock thứ 2 thì cũng sẽ không bị deadlock
			# do release chỉ cho phép chạy khi đã lock ít nhất  1 lần --> Cần xét đã lock tránh lỗi 
			# --> Khi reply sớm hơn lock --> lock.release thì sẽ bỏ qua không nhả--> deadlock
			self.exitClient()
			debug_message('BLOCK MAIN THREAD, WAITING FOR TEARDOWN REPLY')
			lock.acquire()
			lock.release() # Trả về mặc định
		
		self.state = self.SWITCHING
		self.sendRtspRequest(self.SWITCH)
   
			
	def notify_exit_to_server(self):
		self.sendRtspRequest(self.EXIT)
	
	
	def handler(self):
		"""Handler on explicitly closing the GUI window."""
		self.pauseMovie()
		if tkinter.messagebox.askokcancel('Warning!',"Are you sure to quit?"):
			try:
				self.waiting_to_quit = 1
				if self.state != self.INIT:
					lock.acquire()
					self.exitClient() # send TEARDOWN REQUEST
					lock.acquire()
					lock.release()
				self.notify_exit_to_server() # Thông báo cho server thu hồi thread nghe request từ client
				debug_message('CLOSE RTSP SOCKET')
				self.rtspSocket.shutdown(socket.SHUT_RDWR)      # close socket)
				self.rtspSocket.close()  
			except:
				debug_message('SOME THING WAS WRONG')
			self.master.destroy()  # Close the gui window   
			sys.exit()           
		else:  # When the user presses cancel, resume playing.
			self.playMovie()