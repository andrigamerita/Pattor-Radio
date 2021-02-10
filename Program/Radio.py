#!/usr/bin/python3

# -
# | Pattor Radio
# | PiFM-powered pirate radio
# | on the Raspberry Pi, with goodies
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the GPLv3
# -

from os import walk, path, system
from random import randint
from sys import argv
from time import sleep
from mutagen.mp3 import MP3

PlayedSongs = []

UserConfig = {
	"Music file extensions": (".mp3"),
	"Music folder": "Music",
	"Path to PiFM executable": "/home/pi/PiFM/src/pifm",
	"Song replay chance": 5
}

PiFMConfig = {
	"Alternative Frequencies": [],
	"Cutoff Frequency": "",
	"Frequency": "108.0",
	"Frequency Deviation": "",
	"GPIO Pin": "",
	"GPIO Power": "7",
	"Oscillator Errors": "",
	"Output MPX Power": "40",
	"PI-Code": "1055",
	"Preemph": "eu",
	"Program Service Name": "PTTRADIO",
	"Program Type": "15",
	"Radio Text": "Pattor private 0.08W Radio",
	"Traffic information carried": ""
}

"""
# Semi-custom random number generation to deal with the fact that python random.randint is bad.
def RandomInt(Min, Max):
	Factor = randint(Min*Max-Min, Max*Min+Max)
	return int(randint(Min*Factor, Max*Factor)/Factor)
"""

# Function to make sure a song would be replayed accordingly to the user-set replay chance
def RandomSong(TotalSongs):
	global PlayedSongs

	SongIndex = randint(0, TotalSongs-1)

	if SongIndex in PlayedSongs:
		if PlayedSongs.index(SongIndex) < TotalSongs-((TotalSongs/100)*UserConfig["Song replay chance"]):
			SongIndex = RandomSong(TotalSongs)
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
		if not AudioFile.endswith(UserConfig["Music file extensions"]):
			SongList.pop(AudioFile)

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

# Getting duration of an audio file in seconds.
def GetAudioDuration(AudioFile):
	if AudioFile.endswith(".mp3"):
		return MP3(AudioFile).info.length
	else:
		return None

def main():
	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))

	RadioLooping = True

	while RadioLooping:
		CurrentSong = RandomSong(len(SongList))
		CurrentSongDuration = GetAudioDuration(CurrentSong)

		print(
			"Now playing: " + CurrentSong +
			" (" + str(int(CurrentSongDuration)) + "s).\n"
		)

		system(
			"sudo sox -t mp3 \"" + CurrentSong + "\"" +
			" -t wav - | sudo " + UserConfig["Path to PiFM executable"] +
			" --audio -" +
			" --freq " + PiFMConfig["Frequency"] +
			" --pi " + PiFMConfig["PI-Code"] +
			" --ps " + PiFMConfig["Program Service Name"] +
			" --rt \"" + PiFMConfig["Radio Text"] + "\"" +
			" --pty " + PiFMConfig["Program Type"] +
			" --mpx " + PiFMConfig["Output MPX Power"] +
			" --power " + PiFMConfig["GPIO Power"] +
			" --preemph " + PiFMConfig["Preemph"] +
			" &"
		)

		sleep(CurrentSongDuration)
		system("sudo pkill pifm")

		print("")

if  __name__ == "__main__":
	main()
