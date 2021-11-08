import cv2

class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		self.video = cv2.VideoCapture(self.filename)
		
	def nextFrame(self):
		"""Get next frame."""
		
		data = self.file.read(5) # Get the framelength from the first 5 bits
		if data: 
			framelength = int(data)
							
			# Read the current frame
			data = self.file.read(framelength)
			self.frameNum += 1
		return data
		

		
	def frameNbr(self):
		"""Get frame number."""
		return self.frameNum
	
	def take_video_infomation(self):
		cv2video = cv2.VideoCapture(self.filename)
		self.height = cv2video.get(cv2.CAP_PROP_FRAME_HEIGHT)
		self.width  = cv2video.get(cv2.CAP_PROP_FRAME_WIDTH) 
		self.frames_per_second = cv2video.get(cv2.CAP_PROP_FPS)
		self.total_frames = self.count_frames_manual(cv2video)
		#self.total_frames = cv2video.get(cv2.CAP_PROP_FRAME_COUNT) # Không phải lúc nào cũng lấy được
		print(self.total_frames)
		
		self.video_encode = cv2video.getBackendName()
		self.total_duration = self.total_frames / self.frames_per_second

	def count_frames_manual(self, video):
		# initialize the total number of frames read
		total = 0

		# loop over the frames of the video
		while True:
			# grab the current frame
			(grabbed, frame) = video.read()
			
	 
			# check to see if we have reached the end of the
			# video
			if not grabbed:
				break

			# increment the total number of frames read
			total += 1

		# return the total number of frames in the video file
		return total