![Illustration](https://github.com/phananh1010/360-object-detection-annotation/blob/master/illustration.png?raw=true)

# 360ObjectAnnotator: A Tool to Annotate Object Bounding Box for 360 Videos

This is a tool to annotate bounding boxes for object detection in 360 videos. The tool provides a GUI to locate objects in equirectangular images via mouse interaction. 

## Requirements
This tool has been tested in Windows OS. It may not work on Linux. Python2 is required.


## Installation
This program has been tested in the Conda environment. Check `requirement.txt` for all required packages.

## Usage
Create an `images` folder inside the root folder if it has not been created before. Remove all non `images` files such as .txt from the `images` folder.

Go into the root folder of this project and start the program using this command:
```
python main.py
```
After the program runs, the main window will appear showing content of the first image inside the `images` folder in equirectangular format. Move the mouse cursor to the center of the object to be annotated and left click. Another small window will pop up showing the viewport project of a section inside the equirectangular image.

Drag the mouse from top-right to bottom-left to create a bouding box. Type designated key to assign object class to the bounding box. Refer to `config.ini` file for key-class bindings.

Type `a` or `d` to move between images stored inside the 'images' folders

Type `q` to quit the program

## Contact
If you have any questions, please use the public issues section on this GitHub. Alternatively, drop us an e-mail at mailto:anguy59@gmu.edu.

## Ackowledgement
This tool is created with contributions from David Joy. A part of the code is reused from the [Pano2Vid](https://github.com/sammy-su/Pano2Vid) project.
