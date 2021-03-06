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
from Helpers.LoggingHelper import *
from Helpers.IOHelper import *

AudioFileExtensions = (".mp3", ".oga", ".ogg", ".opus", ".wav", ".flac")

PlayedSongs = []
UserConfig, PiFMConfig = {}, {}

# Loading the program configuration files
def LoadConfig():
	global UserConfig, PiFMConfig

	UserConfig = LoadJSON("Config/User.json")
	PiFMConfig = LoadJSON("Config/PiFM.json")

	if UserConfig == None or PiFMConfig == None:
		Logging("E" + "Error loading configuration files. The program will exit.")
		exit()

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

# Saving the list of playeds songs
def SavePlayedSongs():
	global PlayedSongs

	with open("Data/PlayedSongs.list", "w") as PlayedSongsFile:
		for SongIndex in PlayedSongs:
			PlayedSongsFile.write(str(SongIndex) + "\n")

# Loading the list of playeds songs
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
		if AudioFile.album == "" or AudioFile.album == None:
			return ""
		else:
			return AudioFile.album

	elif Info == "Artist":
		if AudioFile.artist == "" or AudioFile.artist == None:
			return ""
		else:
			return AudioFile.artist

	elif Info == "Duration":
		if AudioFile.duration == "" or AudioFile.duration == None:
			return ""
		else:
			return AudioFile.duration

	elif Info == "Title":
		if AudioFile.title == "" or AudioFile.title == None:
			return path.basename(FilePath)
		else:
			return AudioFile.title

# Read file extension of audio file, to let SoX know what type the file is and for the WebUI to work
def GetAudioFileExtension(FilePath):
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

		while SleepCycle < SongDuration:
			if UserConfig["Always refresh configuration"] == True:
				LoadConfig()

			if ReadPlayDirections() == "Pause":
				SongPaused = True
				while SongPaused:
					sleep(UserConfig["Standalone UI enabled [Refresh rate]"])
					if ReadPlayDirections() != "Pause":
						SongPaused = False

			elif ReadPlayDirections() == "Skip":
				TextFileWrite("Data/PlayDirections", "0")
				break

			else:
				TextFileWrite("Data/PlayDirections", str(SleepCycle)) # Quite a bit of time gets wasted when the direction is to Play after a Pause (??); TODO: Something should be fixed in this function, probably the fact that there's shouldn't be any sleep happening after this else condition in the current cycle of the while loop

			sleep(UserConfig["Standalone UI enabled [Refresh rate]"])
			SleepCycle += UserConfig["Standalone UI enabled [Refresh rate]"]

# Program main function
def Main():
	LoadConfig()
	ClearPlayDirections()

	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))

	if UserConfig["Played songs list loading"] == True:
		LoadPlayedSongs() # TODO: Add a way for the program to detect if the song folder's contents changed, or else problems will occour (some songs won't be played).

	RadioLooping = True

	while RadioLooping:
		if UserConfig["Always refresh configuration"] == True:
			LoadConfig()

		CurrentSongIndex = None
		while CurrentSongIndex == None:
			CurrentSongIndex = RandomSong(len(SongList))

		if UserConfig["Played songs list saving"] == True:
			SavePlayedSongs()

		CurrentSongPath = SongList[CurrentSongIndex]
		CurrentSongInfo = {
			"Album": GetAudioInfo(CurrentSongPath, "Album"),
			"Artist": GetAudioInfo(CurrentSongPath, "Artist"),
			"Duration": GetAudioInfo(CurrentSongPath, "Duration"),
			"File Path": CurrentSongPath,
			"File Extension": GetAudioFileExtension(CurrentSongPath),
			"Title": GetAudioInfo(CurrentSongPath, "Title")
		}

		if UserConfig["Standalone UI enabled [Refresh rate]"] != "" or UserConfig["Standalone UI enabled [Refresh rate]"] != None or UserConfig["Standalone UI enabled [Refresh rate]"] != False:
			with open("Data/CurrentSongInfo.json", "w") as CurrentSongInfoFile:
				json.dump(CurrentSongInfo, CurrentSongInfoFile)

		Logging("I",
			"Now playing: " + CurrentSongInfo["Title"] +
			" (" + str(int(CurrentSongInfo["Duration"])) + "s).\n"
		)

		if UserConfig["Using PiFM [Path]"] != "" or UserConfig["Using PiFM [Path]"] != None or UserConfig["Using PiFM [Path]"] != False:
			system(
				"sudo sox -t " + CurrentSongInfo["File Extension"] +
				" \"" + CurrentSongInfo["File Path"] + "\"" +
				" -t wav - | sudo " + UserConfig["Using PiFM [Path]"] +
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

		if UserConfig["Using PiFM [Path]"] != "" or UserConfig["Using PiFM [Path]"] != None or UserConfig["Using PiFM [Path]"] != False:
			system("sudo pkill pifm")

		print("")

if  __name__ == "__main__":
	try:
		Main()

	except KeyboardInterrupt:
		Logging("D", "Stopping Main function.")