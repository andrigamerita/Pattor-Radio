#!/usr/bin/python3

# -
# | Pattor Radio
# | PiFM-powered pirate radio
# | on the Raspberry Pi, with goodies
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the GPLv3
# -

import json
from os import walk, path, system
from random import randint
from sys import argv
from time import sleep
from Include.tinytag import TinyTag
#from mutagen.mp3 import MP3

AudioFileExtensions = (".mp3", ".oga", ".ogg", ".opus", ".wav", ".flac")

PlayedSongs = []
UserConfig, PiFMConfig = {}, {}

"""
# Semi-custom random number generation to deal with the fact that python random.randint is bad.
def RandomInt(Min, Max):
	Factor = randint(Min*Max-Min, Max*Min+Max)
	return int(randint(Min*Factor, Max*Factor)/Factor)
"""

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

	return None

# Loading the program configuration files
def LoadConfig():
	global UserConfig, PiFMConfig

	UserConfig = LoadJSON("Config/User.config")
	PiFMConfig = LoadJSON("Config/PiFM.config")

	if UserConfig == None or PiFMConfig == None:
		print("[E] Error loading configuration files. The program will exit.")
		exit()

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

"""
# Saving the music folder scan on a txt file, for loading it later without rescanning.
def SaveSongList():
	SongList = ScanMusic()

	with open("SongList", "w") as SongListFile:
		SongListFile.write(str(SongList))

	return SongList

# Attempt to load song folder scan saved on text file, only really useful on really slow storages.
def LoadSongList():
	try:
		with open("SongList", "r") as SongListFile:
			return SongListFile.read()
	except:
		return SaveSongList()
"""

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
	if FilePath.endswith(AudioFileExtensions):
		return FilePath[-3:]

# Setting the Radio Text based on user preferences
def PiFMRadioText(SongInfo):
	if PiFMConfig["Radio Text from song info"] == ["Title"]:
		return SongInfo["Title"]
	else:
		return PiFMConfig["Static Radio Text"]

def main():
	LoadConfig()
	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))

	RadioLooping = True

	while RadioLooping:
		CurrentSongIndex = None
		while CurrentSongIndex == None:
			CurrentSongIndex = RandomSong(len(SongList))

		CurrentSong = SongList[CurrentSongIndex]
		CurrentSongInfo = {"Duration":GetAudioInfo(CurrentSong,"Duration"), "Title":GetAudioInfo(CurrentSong, "Title")}

		print(
			"Now playing: " + CurrentSongInfo["Title"] +
			" (" + str(int(CurrentSongInfo["Duration"])) + "s).\n"
		)

		system(
			"sudo sox -t " + SoXFileType(CurrentSong) +
			" \"" + CurrentSong + "\"" +
			" -t wav - | sudo " + UserConfig["Path to PiFM executable"] +
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
