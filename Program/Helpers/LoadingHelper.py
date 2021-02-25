#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
from os import path
from .LoggingHelper import *

# File loading with custom error handling.
def LoadFile(FilePath, FileMode):
	#if FileMode != ("r", "r+", "rb", "rb+" "w", "w+", "wb", "wb+", "a", "a+", "ab", "ab+", "x"):
		#Logging("E", "Error loading file: " + FilePath + ": Unknown FileMode " + FileMode + ".")
		#return None

	if (FileMode.startswith("r") and path.isfile(FilePath)) or FileMode == "w":
		try:
			File = open(FilePath, FileMode)
			return File
		except:
			Logging("E", "Unknown error loading file: " + FilePath + ".")
	else:
		Logging("E", "Error loading file: " + FilePath + " does not exist and mode " + FileMode + " is not creating it.")

	return None

# Reading contents of a text file.
def TextFileRead(FilePath):
	File = LoadFile(FilePath, "r")

	if File == None:
		return None

	FileContent = File.read()
	File.close()

	return FileContent

# Reading contents of a binary file.
def BinaryFileRead(FilePath):
	File = LoadFile(FilePath, "rb")

	if File == None:
		return None

	FileContent = File.read()
	File.close()

	return FileContent

# Loading a JSON string from file.
def LoadJSON(FilePath):
	File = LoadFile(FilePath, "r")

	if File == None:
		return None

	JSON = json.load(File)
	File.close()

	return JSON