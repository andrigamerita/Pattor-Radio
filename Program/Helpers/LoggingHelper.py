#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

# Advanced logging with different levels and types (writing to console or file)
def Logging(LogLevel, Message, LogType):
	if LogType == "Console":
		print("[" + LogLevel + "] " + Message)