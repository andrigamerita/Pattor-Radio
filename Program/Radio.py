#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
from datetime import datetime
from os import walk, path, system
from random import randint
from time import sleep
from Include.tinytag import TinyTag
from Helpers.LoadingHelper import *
from Helpers.LoggingHelper import *

AudioFileExtensions = (".mp3", ".oga", ".ogg", ".opus", ".wav", ".flac")

PlayedSongs = []
UserConfig, PiFMConfig = {}, {}

# Loading a JSON string from file
def LoadJSON(FilePath):
	File = LoadFile(FilePath, "r")

	if File != None:
		JSON = json.load(File)
		File.close()
		return JSON

	File.close()
	return None

# Loading the program configuration files
def LoadConfig():
	global UserConfig, PiFMConfig

	UserConfig = LoadJSON("Config/User.config")
	PiFMConfig = LoadJSON("Config/PiFM.config")

	if UserConfig == None or PiFMConfig == None:
		Logging("E" + "Error loading configuration files. The program will exit.", "Console")
		exit()

# Validating the configurations
#def ValidateConfig():

# Function to make sure a song would be replayed accordingly to the user-set replay space percentage
def RandomSong(TotalSongs):
	global PlayedSongs

	SongIndex = randint(0, TotalSongs-1)

	if SongIndex in PlayedSongs:
		if PlayedSongs.index(SongIndex) < int(TotalSongs-((TotalSongs/100)*UserConfig["Song replay space percentage"]))-1:
			return None
		else:
			PlayedSongs.insert(0, PlayedSongs.pop(SongIndex))
	else:
		PlayedSongs.insert(0, SongIndex)

	return SongIndex

def SavePlayedSongs():
	global PlayedSongs

	with open("Data/PlayedSongs.list", "w") as PlayedSongsFile:
		for SongIndex in PlayedSongs:
			PlayedSongsFile.write(str(SongIndex) + "\n")

def LoadPlayedSongs():
	global PlayedSongs

	PlayedSongsFile = LoadFile("Data/PlayedSongs.list", "r")

	if PlayedSongsFile != None:
		PlayedSongs = [int(SongIndex) for SongIndex in PlayedSongsFile.read().splitlines()]
		PlayedSongsFile.close()

# Scanning of the music folder, including subfolders.
def ScanMusic(MusicFolder):
	SongList = []

	for dirpath, dirnames, filenames in walk(MusicFolder):
		SongList += [path.join(dirpath, file) for file in filenames]

	return SongList

# Cleaning files with unrecognized audio extension out of the songs list, and removing files with extensions not allowed by the user.
def CleanSongList(SongList):
	for AudioFile in SongList:
		if not AudioFile.endswith(AudioFileExtensions):
			SongList.pop(SongList.index(AudioFile))

	if UserConfig["Enabled file extensions"] != "All":
		for AudioFile in SongList:
			if not AudioFile.endswith(tuple(UserConfig["Enabled file extensions"])):
				SongList.pop(SongList.index(AudioFile))

	return SongList

# Getting meaningful information from an audio file
def GetAudioInfo(FilePath, Info):
	AudioFile = TinyTag.get(FilePath)

	if Info == "Album":
		return AudioFile.album
	elif Info == "Artist":
		return AudioFile.artist
	elif Info == "Duration":
		return AudioFile.duration
	elif Info == "Title":
		if AudioFile.title == "":
			return path.basename(FilePath)
		else:
			return AudioFile.title

# Read file extension of audio file, to let SoX know what type the file is
def SoXFileType(FilePath):
	if FilePath.endswith(AudioFileExtensions): # Spagoot, need to unspagoot soon
		if FilePath[-3:] == "lac":
			return "flac"
		elif FilePath[-3:] == "pus":
			return "opus"
		else:
			return FilePath[-3:]

# Setting the Radio Text based on user preferences
def PiFMRadioText(SongInfo):
	RadioTextList = PiFMConfig["Radio Text"]
	RadioText = ""

	for Token in RadioTextList:
		if list(RadioTextList[RadioTextList.index(Token)])[0] == "Custom Text":
			RadioText += RadioTextList[RadioTextList.index(Token)]["Custom Text"]

		elif list(RadioTextList[RadioTextList.index(Token)])[0] == "Song Info":
			if RadioTextList[RadioTextList.index(Token)]["Song Info"] == "Album":
				RadioText += SongInfo["Album"]
			elif RadioTextList[RadioTextList.index(Token)]["Song Info"] == "Artist":
				RadioText += SongInfo["Artist"]
			elif RadioTextList[RadioTextList.index(Token)]["Song Info"] == "Duration":
				RadioText += SongInfo["Duration"]
			elif RadioTextList[RadioTextList.index(Token)]["Song Info"] == "Title":
				RadioText += SongInfo["Title"]

			RadioText += " "

	return RadioText

"""
# Function for the broadcast scheduling system, still in the works and barely tested, prone to bugs.
def Schedule():
	ScheduleCheckRate = UserConfig["Schedule checking rate"]

	for ScheduleItem in UserConfig["Schedule"]:
		ScheduleItemSplit = ScheduleItem.split("|")
		ScheduleItemStartSplit = ScheduleItemSplit[0].split(".")
		ScheduleItemEndSplit = ScheduleItemSplit[1].split(".")

		CurrentTime = datetime.now()

		if (CurrentTime.hour, CurrentTime.minute) < ScheduleItemStartSplit:
			#if (CurrentTime.hour, CurrentTime.minute) < ScheduleItemEndSplit:
			#sleep(ScheduleCheckRate)
			continue
			#else:
		else:
			if (CurrentTime.hour, CurrentTime.minute) < ScheduleItemEndSplit:
				# time range good for playing
			else:

	TimeStart, TimeEnd = [], []

	for Token in ScheduleList:
		if list(ScheduleList[ScheduleList.index(Token)])[0] == "Start":
			TimeStart += ScheduleList[ScheduleList.index(Token)]["Start"]
		elif list(ScheduleList[ScheduleList.index(Token)])[0] == "End":
			TimeEnd += ScheduleList[ScheduleList.index(Token)]["End"]

	CurrentTimeFull = datetime.now()
	CurrentTime = str(CurrentTimeFull.hour) + "." + str(CurrentTimeFull.minute)

	for ListTime in TimeStart:
		if CurrentTime["H"] < TimeStart[ListTime] and CurrentTime["M"] < TimeStart[ListTime]
"""

# Clears playing directions file
def ClearPlayDirections():
	PlayDirectionsFile = LoadFile("Data/PlayDirections", "w")

	if PlayDirectionsFile != None:
		PlayDirectionsFile.write("")
		PlayDirectionsFile.close()

# Reads directions regarding playing statuses the program will follow, read from a local file
def ReadPlayDirections():
	PlayDirectionsFile = LoadFile("Data/PlayDirections", "r")

	if PlayDirectionsFile != None:
		PlayDirections = PlayDirectionsFile.read()
		PlayDirectionsFile.close()
		return PlayDirections

	return None

# Function handling the program idling while a song is playing
def SongSleep(SongDuration):
	if UserConfig["Standalone UI enabled [Refresh rate]"] == "" or UserConfig["Standalone UI enabled [Refresh rate]"] == None or UserConfig["Standalone UI enabled [Refresh rate]"] == False:
		sleep(SongDuration)

	else:
		SleepCycle = 0.0
		print(SongDuration)

		while SleepCycle < SongDuration/UserConfig["Standalone UI enabled [Refresh rate]"]:
			if UserConfig["Always refresh configuration"] == True:
				LoadConfig()

			if ReadPlayDirections() == "Pause":
				SongPaused = True
				while SongPaused:
					sleep(UserConfig["Standalone UI enabled [Refresh rate]"])
					if ReadPlayDirections() != "Pause":
						SongPaused = False

			elif ReadPlayDirections() == "Skip":
				ClearPlayDirections()
				break

			sleep(UserConfig["Standalone UI enabled [Refresh rate]"])
			SleepCycle += 1
			print(SleepCycle)

	return "Done"

# Program main function
def Main():
	LoadConfig()
	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))

	if UserConfig["Played songs list loading"] == True:
		LoadPlayedSongs()

	RadioLooping = True

	while RadioLooping:
		if UserConfig["Always refresh configuration"] == True:
				LoadConfig()

		#if UserConfig["Schedule"] != "" or UserConfig["Schedule"] != None or UserConfig["Schedule"] != False:
			#Schedule()

		CurrentSongIndex = None
		while CurrentSongIndex == None:
			CurrentSongIndex = RandomSong(len(SongList))

		if UserConfig["Played songs list saving"] == True:
			SavePlayedSongs()

		CurrentSong = SongList[CurrentSongIndex]
		CurrentSongInfo = {
			"Album": GetAudioInfo(CurrentSong,"Album"),
			"Artist": GetAudioInfo(CurrentSong,"Artist"),
			"Duration": GetAudioInfo(CurrentSong,"Duration"),
			"Title": GetAudioInfo(CurrentSong, "Title")
		}

		Logging("I",
			"Now playing: " + CurrentSongInfo["Title"] +
			" (" + str(int(CurrentSongInfo["Duration"])) + "s).\n",
			"Console"
		)

		if UserConfig["Using PiFM [path]"] != "" or UserConfig["Using PiFM [path]"] != None or UserConfig["Using PiFM [path]"] != False:
			system(
				"sudo sox -t " + SoXFileType(CurrentSong) +
				" \"" + CurrentSong + "\"" +
				" -t wav - | sudo " + UserConfig["Using PiFM [path]"] +
				" --audio -" +
				" --freq " + PiFMConfig["Frequency"] +
				" --pi " + PiFMConfig["PI-Code"] +
				" --ps " + PiFMConfig["Program Service Name"] +
				" --rt \"" + PiFMRadioText(CurrentSongInfo) + "\"" +
				" --pty " + PiFMConfig["Program Type"] +
				" --mpx " + PiFMConfig["Output MPX Power"] +
				" --power " + PiFMConfig["GPIO Power"] +
				" --preemph " + PiFMConfig["Preemph"] +
				" &"
			)

		SongSleep(CurrentSongInfo["Duration"])

		if UserConfig["Using PiFM [path]"] != "" or UserConfig["Using PiFM [path]"] != None or UserConfig["Using PiFM [path]"] != False:
			system("sudo pkill pifm")

		print("")

if  __name__ == "__main__":
	Main()