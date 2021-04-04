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
from http.server import BaseHTTPRequestHandler
from Include.multithread_http_server import MultiThreadHttpServer
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
	if UserConfig["Remote UI enabled [Refresh rate]"] == "" or UserConfig["Remote UI enabled [Refresh rate]"] == None or UserConfig["Remote UI enabled [Refresh rate]"] == False:
		sleep(SongDuration)

	else:
		SleepCycle = 0.0

		while SleepCycle < SongDuration:
			if UserConfig["Always refresh configuration"] == True:
				LoadConfig()

			if ReadPlayDirections() == "Pause":
				SongPaused = True
				while SongPaused:
					sleep(UserConfig["Remote UI enabled [Refresh rate]"])
					if ReadPlayDirections() != "Pause":
						SongPaused = False

			elif ReadPlayDirections() == "Skip":
				sleep(UserConfig["Remote UI enabled [Refresh rate]"])
				TextFileWrite("Data/PlayDirections", "")
				break

			else:
				TextFileWrite("Data/PlayDirections", str(SleepCycle))
				SleepCycle += UserConfig["Remote UI enabled [Refresh rate]"]
				sleep(UserConfig["Remote UI enabled [Refresh rate]"])

# Detects config key types to provide a proper token to the WriteConfig function.
def ConfigKeyToken(ConfigKeyValue):
	if type(ConfigKeyValue) == int or type(ConfigKeyValue) == float or type(ConfigKeyValue) == bool:
		return ""

	elif type(ConfigKeyValue) == str:
		return "\""

	elif type(ConfigKeyValue) == list:
		return "["

	elif type(ConfigKeyValue) == dict:
		return "{"

	return None

def ConfigKeyValueToString(ConfigKeyValue):
	if type(ConfigKeyValue) == bool:
		return str(ConfigKeyValue).lower()
	else:
		return str(ConfigKeyValue)

# Rewriting configuration file after some changes.
def WriteConfig(ConfigFilePath, ConfigKey, ConfigKeyNewValue):
	ConfigFileContent = TextFileRead(ConfigFilePath)

	if ConfigFileContent == None:
		return None

	ConfigJSONContent = LoadJSON(ConfigFilePath)

	TextFileWrite(
		ConfigFilePath,
		ConfigFileContent.replace(
			"\"" + ConfigKey + "\": " + ConfigKeyToken(ConfigJSONContent[ConfigKey]) + ConfigKeyValueToString(ConfigJSONContent[ConfigKey]),
			"\"" + ConfigKey + "\": " + ConfigKeyToken(ConfigKeyNewValue) + ConfigKeyValueToString(ConfigKeyNewValue)
		)
	)

# Patching the Base HTML file with the specific page template desired.
def PatchHTML(TemplateFilePath):
	TemplateContent = TextFileRead(TemplateFilePath)

	if TemplateContent == None:
		return None

	PatchedHTML = BaseHTML.replace("[HTML:BodyMain]", TemplateContent)

	try:
		if WebUITitles[path.basename(TemplateFilePath).replace(".html", "")] == None:
			return PatchedHTML.replace("[HTML:Title]", "")
		else:
			return PatchedHTML.replace("[HTML:Title]", WebUITitles[path.basename(TemplateFilePath).replace(".html", "")])
	except:
		return PatchedHTML

# Writing playing directions to file for the main program to read.
def WritePlayDirections(PlayDirection):
	PlayDirectionsFile = LoadFile("Data/PlayDirections", "w")

	if PlayDirectionsFile == None:
		return None

	PlayDirectionsFile.write(PlayDirection)
	PlayDirectionsFile.close()

# Reading GET requests and responding accordingly.
def ReadGETParameters(RequestPath):
	if RequestPath == "/" or RequestPath == "/index.html":
		return PatchHTML("Program/WebUI/Templates/Main.html").encode("utf-8")

	elif RequestPath == "/404" or RequestPath == "/404.html":
		return PatchHTML("Program/WebUI/Templates/404.html").encode("utf-8")

	elif RequestPath == "/manifest.json" or RequestPath == "/manifest.webmanifest":
		return BinaryFileRead("Program/WebUI/manifest.json")

	elif (RequestPath.startswith("/icon-") or RequestPath.startswith("/favicon.")) and RequestPath.endswith(".png"):
		return BinaryFileRead("Assets" + RequestPath)

	elif (RequestPath.startswith("/style/")):
		if RequestPath.endswith((".css", ".woff2", ".txt")) and not ".." in RequestPath:
			return BinaryFileRead("Program/WebUI" + RequestPath)

	elif RequestPath.startswith("/AudioStream".lower()):
		LoadConfig()

		if UserConfig["HTTP Audio Streaming"] == True:
			CurrentSongInfo = LoadJSON("Data/CurrentSongInfo.json")
			return BinaryFileRead(CurrentSongInfo["File Path"])
		else:
			return "HTTP Audio Streaming is disabled as per user configuration.".encode("utf-8")

	elif RequestPath == "/HTTPAudio".lower() or RequestPath == "/HTTPAudio.html".lower():
		LoadConfig()

		if UserConfig["HTTP Audio Streaming"] == True:
			return TextFileRead("Program/WebUI/Forms/HTTPAudio.html").replace("[JS:RefreshRate]", str(UserConfig["Remote UI enabled [Refresh rate]"])).replace("[HTML:WebUIAudioVolume]", str(UserConfig["WebUI Streaming Default Volume"])).encode("utf-8")
		else:
			return "HTTP Audio Streaming is disabled as per user configuration.".encode("utf-8")

	elif RequestPath == "/CurrentSongInfo".lower() or RequestPath == "/CurrentSongInfo.json".lower():
		return LoadJSON("Data/CurrentSongInfo.json")

	elif RequestPath.startswith("/PlayDirections".lower()):
		return BinaryFileRead("Data/PlayDirections")

	elif RequestPath == "/?ActionPage=RemoteControls".lower():
		return BinaryFileRead("Program/WebUI/Forms/RemoteControls.html")

	elif RequestPath == "/?ActionPage=SkipSongs".lower():
		return BinaryFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath.startswith("/?RunAction=SkipSongs".lower()):
		WritePlayDirections("Skip")
		return BinaryFileRead("Program/WebUI/Forms/RemoteControls.html")

	elif RequestPath == "/?ActionPage=PlayPauseSong".lower():
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

	elif RequestPath.startswith("/?RunAction=PauseSong".lower()):
		WritePlayDirections("Pause")
		return BinaryFileRead("Program/WebUI/Forms/RemoteControls.html")

	elif RequestPath.startswith("/?RunAction=PlaySong".lower()):
		WritePlayDirections("Play")
		return BinaryFileRead("Program/WebUI/Forms/RemoteControls.html")

	elif RequestPath == "/?ActionPage=ConfigManager".lower():
		if UserConfig["PiFM Enabled"]:
			return TextFileRead("Program/WebUI/Forms/ConfigManager.html").replace("[HTML:ConfigEnableDisablePiFM]", "Disable").encode("utf-8")
		else:
			return TextFileRead("Program/WebUI/Forms/ConfigManager.html").replace("[HTML:ConfigEnableDisablePiFM]", "Enable").encode("utf-8")

	elif RequestPath.startswith("/?RunAction=EnableDisablePiFM".lower()):
		if UserConfig["PiFM Enabled"]:
			UserConfig["PiFM Enabled"] = False
			WriteConfig("Config/User.json", "PiFM Enabled", False)
			return TextFileRead("Program/WebUI/Forms/ConfigManager.html").replace("[HTML:ConfigEnableDisablePiFM]", "Enable").encode("utf-8")
		else:
			UserConfig["PiFM Enabled"] = True
			WriteConfig("Config/User.json", "PiFM Enabled", True)
			return TextFileRead("Program/WebUI/Forms/ConfigManager.html").replace("[HTML:ConfigEnableDisablePiFM]", "Disable").encode("utf-8")

	return None

# Setting response content type based on file extension.
def SetContentType(RequestPath):
	if RequestPath.endswith(".png"):
		return "image/png"

	elif RequestPath.endswith(".json"):
		return "application/json"

	elif RequestPath.endswith(".txt"):
		return "text/plain"

	elif RequestPath.endswith(".css"):
		return "text/css"

	elif RequestPath.endswith(".woff2"):
		return "font/woff2"

	elif RequestPath.startswith("/AudioStream/".lower()):
		CurrentSongInfo = LoadJSON("Data/CurrentSongInfo.json")
		if CurrentSongInfo["File Path"].endswith(".wav"):
			return "audio/vnd.wav"
		elif CurrentSongInfo["File Path"].endswith(".mp3"):
			return "audio/mpeg"
		elif CurrentSongInfo["File Path"].endswith(".ogg"):
			return "audio/ogg"

	return "text/html"

# Server main operational class.
class ServerClass(BaseHTTPRequestHandler):
	def SetResponse(self, ResponseCode, ContentType, NoCache=False):
		self.send_response(ResponseCode)
		self.send_header("Content-type", ContentType)
		if NoCache:
			self.send_header("Pragma", "no-cache")
		self.end_headers()

	def do_GET(self):
		ResponseContent = ReadGETParameters(self.path.lower())
		ContentType = SetContentType(self.path.lower())

		if ResponseContent == None:
			self.SetResponse(404, "text/html")
			ResponseContent = PatchHTML("Program/WebUI/Templates/404.html").replace("[HTML:RequestPath]", self.path).encode("utf-8")
		else:
			if self.path == "/HTTPAudio".lower() or self.path == "/HTTPAudio.html".lower() or self.path == "/AudioStream".lower():
				self.SetResponse(200, ContentType, NoCache=True)
			else:
				self.SetResponse(200, ContentType)

		if ResponseContent != None:
			self.wfile.write(ResponseContent)

# Program main function
def Main():
	ThisCycleUsePiFM = False
	ClearPlayDirections()
	SongList = CleanSongList(ScanMusic(UserConfig["Music folder"]))

	if UserConfig["Played songs list loading"] == True:
		LoadPlayedSongs() # TODO: Add a way for the program to detect if the song folder's contents changed, or else problems will occour (some songs won't be played).

	while True:
		if UserConfig["Always refresh configuration"] == True:
			LoadConfig()

		CurrentSongIndex = None
		while CurrentSongIndex == None:
			CurrentSongIndex = RandomSong(len(SongList))

		if UserConfig["Played songs list saving"] == True:
			SavePlayedSongs()

		CurrentSongInfo = {
			"Album": GetAudioInfo(SongList[CurrentSongIndex], "Album"),
			"Artist": GetAudioInfo(SongList[CurrentSongIndex], "Artist"),
			"Duration": GetAudioInfo(SongList[CurrentSongIndex], "Duration"),
			"File Path": SongList[CurrentSongIndex],
			"File Extension": GetAudioFileExtension(SongList[CurrentSongIndex]),
			"Title": GetAudioInfo(SongList[CurrentSongIndex], "Title")
		}

		if CurrentSongInfo["Duration"] == "":
			Logging("I", "Duration not found in current song (" + CurrentSongInfo["File Path"] + "); Is the format supported?")
			continue

		if UserConfig["Remote UI enabled [Refresh rate]"] != "" and UserConfig["Remote UI enabled [Refresh rate]"] != None and UserConfig["Remote UI enabled [Refresh rate]"] != False:
			with open("Data/CurrentSongInfo.json", "w") as CurrentSongInfoFile:
				json.dump(CurrentSongInfo, CurrentSongInfoFile)

		Logging("I",
			"Now playing: " + CurrentSongInfo["Title"] +
			" (" + str(int(CurrentSongInfo["Duration"])) + "s).\n"
		)

		if UserConfig["PiFM Enabled"]:
			ThisCycleUsePiFM = True

			system(
				"sudo sox -t " + CurrentSongInfo["File Extension"] +
				" \"" + CurrentSongInfo["File Path"] + "\"" +
				" -t wav - | sudo " + UserConfig["PiFM Path"] +
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

		if ThisCycleUsePiFM:
			system("sudo pkill pifm")
			ThisCycleUsePiFM = False

		print("")

if  __name__ == "__main__":
	try:
		Logging("D", "Starting Pattor Radio Server.")
		LoadConfig()

		if UserConfig["Remote UI enabled [Refresh rate]"] == "" or UserConfig["Remote UI enabled [Refresh rate]"] == None or UserConfig["Remote UI enabled [Refresh rate]"] == False:
			Logging("D", "WebUI is not starting as per user configuration flags.")
		else:
			BaseHTML = TextFileRead("Program/WebUI/Base.html")
			if BaseHTML == None:
				Logging("D", "Couldn't load contents from Base HTML File. WebUI might be broken.")
				BaseHTML = "[HTML:BodyMain]"

			WebUITitlesFile = LoadFile("Program/WebUI/Titles.json", "r")
			if WebUITitlesFile == None:
				Logging("D", "Couldn't load WebUI Titles File. WebUI might be broken.")
			else:
				WebUITitles = json.load(WebUITitlesFile)
				WebUITitlesFile.close()

			Server = MultiThreadHttpServer(tuple(UserConfig["HTTP Address"]), 16, ServerClass)
			Logging("D", "Starting HTTP Server on address " + str(UserConfig["HTTP Address"]))
			Server.start(background=True)

		Main()

	except KeyboardInterrupt:
		Logging("D", "Stopping Pattor Radio Server.")

		if UserConfig["Remote UI enabled [Refresh rate]"] != "" or UserConfig["Remote UI enabled [Refresh rate]"] != None or UserConfig["Remote UI enabled [Refresh rate]"] != False:
			Server.stop()