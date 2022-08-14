import cv2
import os
from re import sub as regex_sub
import numpy as np
from win32api import GetSystemMetrics
from VideoRecorder import ImageRecorder

class Annotator:
	colors = {-1:(255,255,255)}	#set in main.py
	names = {-1:""}				#set in main.py
	keys = dict()				#set in main.py
	view_angle = 65.5

	def __init__(self, filepath, config):	#image is located at path+filename from this folder
		#load the image and calculate sizes
		self.config = config
		self.filepath = filepath
		self.annotations = self.load() if os.path.exists(self.filepath.replace(self.config.get("image_ending", ".png"), ".txt")) else []
		self.viewport = None
		self.name = regex_sub("^.*/", "", filepath)
		self.image = cv2.imread(filepath)	#if statement allows path to end with slash or not
		self.anno_image = self.image
		self.sphereH, self.sphereW, _ = map(int, self.image.shape)	#height and width of the input image
		screen_width = GetSystemMetrics(0)
		scale = float(screen_width) / self.sphereW	#screen width divided by total width of image.  Used for determining height to maintain aspect ratio
		
		#create	the window and display the image:
		cv2.namedWindow(self.name, cv2.WINDOW_NORMAL)
		cv2.resizeWindow(self.name, screen_width, int(np.ceil(scale * self.sphereH)))
		cv2.moveWindow(self.name, 0, config.getint("window_top", 0))
		self.render()

	def render(self):
		self.anno_image = self.image.copy()
		for (type_num, p1, p2, p3, p4) in self.annotations:
			for (pt_a, pt_b) in ((p1, p2), (p1, p3), (p2, p4), (p3, p4)):
				if abs(pt_a[0] - pt_b[0]) > np.pi: #wraparound, requires two lines
					pt_a, pt_b = max(pt_a, pt_b, key=lambda x:x[0]), min(pt_a, pt_b, key=lambda x:x[0])
					cv2.line(self.anno_image, self.angle_coords(pt_a), self.angle_coords((pt_b[0] + 2*np.pi, pt_b[1])), Annotator.colors[type_num], 3)
					cv2.line(self.anno_image, self.angle_coords(pt_b), self.angle_coords((pt_a[0] - 2*np.pi, pt_a[1])), Annotator.colors[type_num], 3)
				else:
					cv2.line(self.anno_image, self.angle_coords(pt_a), self.angle_coords(pt_b), Annotator.colors[type_num], 3)
		cv2.imshow(self.name, self.anno_image)

	def angle_coords(self, point):	#turns radians into screen coordinates for the equirectangular image
		return (int(self.sphereW*(point[0]+np.pi) / (2 * np.pi)), int(self.sphereH*(np.pi/2 - point[1]) / np.pi))

	#runs controls until user switches images or quits, returns "left", "right", or "quit" depending on how the user closed the window
	def run(self):
		cv2.setMouseCallback(self.name, self.openViewport)
		while True:
			key = cv2.waitKey(0)
			#check if pressed key matches any control keys:
			if key==ord(self.config.get("quit", "Q").lower()):
				self.save()
				return "quit"
			elif key==ord(self.config.get("left", "A").lower()):
				self.save()
				return "left"
			elif key==ord(self.config.get("right", "D").lower()):
				self.save()
				return "right"
			elif key==ord(self.config.get("zoom_in", "W").lower()):
				Annotator.view_angle = 65.5 if Annotator.view_angle == 104.3 else 46.4
			elif key==ord(self.config.get("zoom_out", "S").lower()):
				Annotator.view_angle = 65.5 if Annotator.view_angle == 46.4 else 104.3
			elif key==ord(self.config.get("close_viewport", "E").lower()):
				cv2.destroyWindow("viewport")
			elif key==ord(self.config.get("undo", "Z").lower()):
				if self.viewport is not None and len(self.viewport.annotations) > 0:
					self.viewport.annotations.pop()
					self.viewport.render()
				if len(self.annotations) > 0:
					self.annotations.pop()
					self.render()
			elif key in Annotator.keys:
				category = Annotator.keys[key]
				if self.viewport is not None and len(self.viewport.annotations) > 0:
					self.viewport.annotations[-1][0] = category
					self.viewport.render()
				if len(self.annotations) > 0:
					self.annotations[-1][0] = category
					self.render()

	def openViewport(self, event, x, y, flags, param):
		if event==cv2.EVENT_LBUTTONDOWN:
			cv2.destroyWindow("viewport")
			self.viewport = Viewport(self.getXTheta(x), self.getYTheta(y), Annotator.view_angle, self, self.config)

	def getXTheta(self, x):
		theta_x = (2.* x - 1.) / self.sphereW - 1.
		return theta_x * np.pi
	def getYTheta(self, y):
		theta_y = 0.5 - (y - 0.5) / self.sphereH
		return theta_y * np.pi

	def load(self):
		annos = []
		with open(self.filepath.replace(self.config.get("image_ending", ".png"), ".txt"), "r") as f:	#TODO: Regex
			for line in f.readlines():
				inarr = line.strip().split(" ")
				annos.append([int(inarr[0])] + [(float(inarr[i]), float(inarr[i+1])) for i in range(1, 9, 2)])
		return annos

	def save(self):
		cv2.destroyAllWindows()
		if len(self.annotations) > 0:
			with open(self.filepath.replace(self.config.get("image_ending", ".png"), ".txt"), "w+") as f:	#TODO: Regex
				f.write("\n".join("{} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f} {:.4f}".format(type_num, p1[0], p1[1], p2[0], p2[1], p3[0], p3[1], p4[0], p4[1])
					for (type_num, p1, p2, p3, p4) in self.annotations))
		else:
			if os.path.exists(self.filepath.replace(self.config.get("image_ending", ".png"), ".txt")):
				os.remove(self.filepath.replace(self.config.get("image_ending", ".png"), ".txt"))

class Viewport:
	def __init__(self, theta_x, theta_y, view_angle, parent, config):
		self.config = config
		self.parent = parent
		self.annotations = []
		self.anno_start = None
		#generate viewport image:
		ir = ImageRecorder(parent.sphereW, parent.sphereH, view_angle, config.getint("viewport_width", 640))
		self.x_angles, self.y_angles = ir._direct_camera(theta_x, theta_y)
		self.image = ir.catch(theta_x, theta_y, parent.anno_image)
		self.image[self.image>255.] = 255.
		self.image[self.image<0.] = 0.
		self.image = self.image.astype(np.uint8)
		#open viewport window:
		cv2.namedWindow("viewport", cv2.WINDOW_NORMAL)
		cv2.resizeWindow("viewport", self.image.shape[1], self.image.shape[0])
		cv2.imshow("viewport", self.image)
		cv2.setMouseCallback("viewport", self.annotate)

	def render(self):
		image = self.image.copy()
		for (type_num, min_x, max_x, min_y, max_y) in self.annotations:	#viewport stores annotations in viewport pixels
			cv2.rectangle(image, (min_x, min_y), (max_x, max_y), Annotator.colors[type_num], 2)
			if type_num > -1:	#-1 is the in-progress annotation
				cv2.putText(image, Annotator.names[type_num], (min_x, min_y-3), cv2.FONT_HERSHEY_SIMPLEX, 0.3, Annotator.colors[type_num], 1)
		cv2.imshow("viewport", image)

	def annotate(self, event, x, y, flags, param):
		if event==cv2.EVENT_LBUTTONDOWN:
			self.anno_start = (x, y)
		elif event==cv2.EVENT_LBUTTONUP:
			min_x = min(self.anno_start[0], x)
			max_x = max(self.anno_start[0], x)
			min_y = min(self.anno_start[1], y)
			max_y = max(self.anno_start[1], y)
			self.anno_start = None	#used when moving mouse

			self.annotations.append([1, min_x, max_x, min_y, max_y])
			self.render()
			self.parent.annotations.append([1,
				(self.x_angles[min_y][min_x], self.y_angles[min_y][min_x]),
				(self.x_angles[min_y][max_x], self.y_angles[min_y][max_x]),
				(self.x_angles[max_y][min_x], self.y_angles[max_y][min_x]),
				(self.x_angles[max_y][max_x], self.y_angles[max_y][max_x])])
			self.parent.render()
		elif event==cv2.EVENT_MOUSEMOVE and self.anno_start is not None:	#show in-progress annotation
			self.annotations.append([-1, min(self.anno_start[0], x), max(self.anno_start[0], x), min(self.anno_start[1], y), max(self.anno_start[1], y)])
			self.render()
			self.annotations.pop()