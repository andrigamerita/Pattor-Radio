#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
from os.path import basename
from sys import argv
from http.server import BaseHTTPRequestHandler
from Include.multithread_http_server import MultiThreadHttpServer
from Helpers.LoggingHelper import *
from Helpers.IOHelper import *

UserConfig = {}

# Loading the program configuration files.
def LoadConfig():
	global UserConfig

	UserConfig = LoadJSON("Config/User.json")

	if UserConfig == None:
		Logging("E" + "Error loading configuration files. The program will exit.")
		exit()

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
		if WebUITitles[basename(TemplateFilePath).replace(".html", "")] == None:
			return PatchedHTML.replace("[HTML:Title]", "")
		else:
			return PatchedHTML.replace("[HTML:Title]", WebUITitles[basename(TemplateFilePath).replace(".html", "")])
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

	elif (RequestPath.startswith("/Style/".lower())):
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

	elif RequestPath == "/?ActionPage=SkipSongs".lower():
		return BinaryFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath.startswith("/?RunAction=SkipSongs".lower()):
		WritePlayDirections("Skip")
		return BinaryFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath == "/?ActionPage=PlayPauseSong".lower():
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

	elif RequestPath.startswith("/?RunAction=PauseSong".lower()):
		WritePlayDirections("Pause")
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

	elif RequestPath.startswith("/?RunAction=PlaySong".lower()):
		WritePlayDirections("Play")
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

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

# Main function running the server.
def RunServer():
	Server = MultiThreadHttpServer(("", UserConfig["HTTP Port"]), 16, ServerClass)
	Logging("D", "Starting HTTP Server on port " + str(UserConfig["HTTP Port"]))

	try:
		Server.start()

	except KeyboardInterrupt:
		Logging("D", "Stopping HTTP Server.")
		Server.stop()

if  __name__ == "__main__":
	LoadConfig()
	if UserConfig["Remote UI enabled [Refresh rate]"] == "" or UserConfig["Remote UI enabled [Refresh rate]"] == None or UserConfig["Remote UI enabled [Refresh rate]"] == False:
		Logging("D", "WebUI is not starting as per user configuration flags.")
		exit()

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

	RunServer()