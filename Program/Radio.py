#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
from os import walk, path, system
from random import randint
from sys import argv
from time import sleep
from Include.tinytag import TinyTag

AudioFileExtensions = (".mp3", ".oga", ".ogg", ".opus", ".wav", ".flac")

PlayedSongs = []
UserConfig, PiFMConfig = {}, {}

# File loading with custom error handling
def LoadFile(FilePath, FileMode):
	if path.isfile(FilePath):
		try:
			File = open(FilePath, FileMode)
			return File
		except:
			print("[E] Unknown error loading file: " + FilePath + ".")
	else:
		print("[E] Error loading file: " + FilePath + " does not exist.")

	return None

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
		print("[E] Error loading configuration files. The program will exit.")
		exit()

# Validating the configurations
#def ValidateConfig():

# Function to make sure a song would be replayed accordingly to the user-set replay chance
def RandomSong(TotalSongs):
	global PlayedSongs

	SongIndex = randint(0, TotalSongs-1)

	if SongIndex in PlayedSongs:
		if PlayedSongs.index(SongIndex) < int(TotalSongs-((TotalSongs/100)*UserConfig["Song replay chance"]))-1:
			return None
		else:
			PlayedSongs.insert(0, PlayedSongs.pop(SongIndex))
	else:
		PlayedSongs.insert(0, SongIndex)

	return SongIndex

def SavePlayedSongs():
	if UserConfig["Played songs list saving"] == True:
		global PlayedSongs

		with open("Data/PlayedSongs.list", "w") as PlayedSongsFile:
			for SongIndex in PlayedSongs:
				PlayedSongsFile.write(str(SongIndex) + "\n")

def LoadPlayedSongs():
	if UserConfig["Played songs list loading"] == True:
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

# Cleaning files with unrecognized audio extension out of the songs list.
def CleanSongList(SongList):
	for AudioFile in SongList:
		if not AudioFile.endswith(AudioFileExtensions):
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
	if PiFMConfig["Radio Text from song info"] == ["Title"]:
		return SongInfo["Title"]
	else:
		return PiFMConfig["Static Radio Text"]
	"""

def main():
	LoadConfig()
	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))
	LoadPlayedSongs()

	RadioLooping = True

	while RadioLooping:
		CurrentSongIndex = None
		while CurrentSongIndex == None:
			CurrentSongIndex = RandomSong(len(SongList))

		SavePlayedSongs()

		CurrentSong = SongList[CurrentSongIndex]
		CurrentSongInfo = {
			"Album": GetAudioInfo(CurrentSong,"Album"),
			"Artist": GetAudioInfo(CurrentSong,"Artist"),
			"Duration": GetAudioInfo(CurrentSong,"Duration"),
			"Title": GetAudioInfo(CurrentSong, "Title")
		}

		print(
			"Now playing: " + CurrentSongInfo["Title"] +
			" (" + str(int(CurrentSongInfo["Duration"])) + "s).\n"
		)

		if UserConfig["Using PiFM"] != "" or UserConfig["Using PiFM"] != None:
			system(
				"sudo sox -t " + SoXFileType(CurrentSong) +
				" \"" + CurrentSong + "\"" +
				" -t wav - | sudo " + UserConfig["Using PiFM"] +
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

			sleep(CurrentSongInfo["Duration"])
			system("sudo pkill pifm")

		print("")

if  __name__ == "__main__":
	main()
