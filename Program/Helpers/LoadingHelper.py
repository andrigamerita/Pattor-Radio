#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

from os import path
from .LoggingHelper import *

# File loading with custom error handling
def LoadFile(FilePath, FileMode):
	if path.isfile(FilePath):
		try:
			File = open(FilePath, FileMode)
			return File
		except:
			Logging("E", "Unknown error loading file: " + FilePath + ".")
	else:
		Logging("E", "Error loading file: " + FilePath + " does not exist.")

	return None