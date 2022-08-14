from configparser import ConfigParser
from annotator import Annotator
import os

IMAGE_ENDINGS = (".png", ".jpg", ".jpeg")

def get_all_images(path, images):
	image_set = set()
	anno_set = set()
	for f in os.listdir(path):
		if any(f.endswith(ending) for ending in IMAGE_ENDINGS):
			image_set.add(path+f)
		elif f.endswith(".txt"):
			anno_set.add((path+f).replace(".txt", ".png"))	#TODO: config image ending
		else:	#folder
			get_all_images(path+f+"/", images)
	images.extend((f, f in anno_set) for f in sorted(list(image_set)))

def get_unannotated_index(images):
	for i, (f, annotated) in enumerate(images):
		if not annotated:
			return i

config = ConfigParser()
config.read("config.ini")
config = config["config"]
#load categories:
i = 1
while config.get("anno{}_name".format(i), None) is not None:
	Annotator.colors[i] = (config.getint("anno{}_blue".format(i)), config.getint("anno{}_green".format(i)), config.getint("anno{}_red".format(i)))
	Annotator.names[i] = config.get("anno{}_name".format(i))
	Annotator.keys[ord(config.get("anno{}_key".format(i)).lower())] = i
	i += 1

path = config.get("path")
if path[-1] != "/" and path[-1] != "\\":
	path += "/"

images = []
get_all_images(path, images)

cur_image = get_unannotated_index(images)
while True:
	result = Annotator(images[cur_image][0], config).run()
	if result=="quit":
		exit()
	cur_image = (cur_image + (1 if result=="right" else -1)) % len(images)