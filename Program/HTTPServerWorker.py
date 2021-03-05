#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from os.path import basename
from sys import argv
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
	if type(ConfigKeyValue) == int or type(ConfigKeyValue) == float:
		return ""

	elif type(ConfigKeyValue) == str:
		return "\""

	elif type(ConfigKeyValue) == list:
		return "["

	elif type(ConfigKeyValue) == dict:
		return "{"

	return None

# Rewriting configuration file after some changes.
def WriteConfig(ConfigFilePath, ConfigKey, ConfigKeyNewValue):
	ConfigFileContent = TextFileRead(ConfigFilePath)

	if ConfigFileContent == None:
		return None

	ConfigJSONContent = LoadJSON(ConfigFilePath)

	if TextFileWrite(
		ConfigFilePath,
		ConfigFileContent.replace(
			"\"" + ConfigKey + "\": " + ConfigKeyToken(ConfigJSONContent[ConfigKey]) + str(ConfigJSONContent[ConfigKey]),
			"\"" + ConfigKey + "\": " + ConfigKeyToken(ConfigJSONContent[ConfigKey]) + str(ConfigKeyNewValue)
		)
	) == None:
		return None

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
	PlayDirectionsFile = LoadFile("Data/PlayDirections", "r+")

	if PlayDirectionsFile == None:
		return None

	if PlayDirection == "PlayPause":
		if PlayDirectionsFile.read() == "Pause":
			PlayDirectionsFile.write("Play")
		else:
			PlayDirectionsFile.write("Pause")

	else:
		PlayDirectionsFile.write(PlayDirection)

	PlayDirectionsFile.close()

# Reading GET requests and responding accordingly.
def ReadGETParameters(RequestPath):
	if RequestPath == "/" or RequestPath == "/index.html":
		return PatchHTML("Program/WebUI/Templates/Main.html").encode("utf-8")

	elif RequestPath == "/404" or RequestPath == "/404.html":
		return PatchHTML("Program/WebUI/Templates/404.html").encode("utf-8")

	elif RequestPath == "/manifest.json":
		return BinaryFileRead("Program/WebUI/manifest.json")

	elif (RequestPath.startswith("/icon-") or RequestPath.startswith("/favicon.")) and RequestPath.endswith(".png"):
		return BinaryFileRead("Assets" + RequestPath)

	elif RequestPath == "/AudioStream".lower():
		LoadConfig()

		if UserConfig["HTTP Streaming"] == "" or UserConfig["HTTP Streaming"] == None or UserConfig["HTTP Streaming"] == False:
			return "".encode("utf-8")
		else:
			CurrentSongInfo = LoadJSON("Data/CurrentSongInfo.json")
			return BinaryFileRead(CurrentSongInfo["File Path"])

	elif RequestPath == "/httpaudio" or RequestPath == "/httpaudio.html":
		return TextFileRead("Program/WebUI/Forms/HTTPAudio.html").replace("[JS:RefreshRate]", str(UserConfig["Standalone UI enabled [Refresh rate]"])).encode("utf-8")

	elif RequestPath == "/?ActionPage=SkipSongs".lower():
		return BinaryFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath.startswith("/?RunAction=SkipSongs".lower()):
		WritePlayDirections("Skip")
		return BinaryFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath == "/?ActionPage=PlayPauseSong".lower():
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

	elif RequestPath.startswith("/?RunAction=PlayPauseSong".lower()):
		WritePlayDirections("PlayPause")
		return BinaryFileRead("Program/WebUI/Forms/PlayPauseSong.html")

	return None

# Setting response content type based on file extension.
def SetContentType(RequestPath):
	if RequestPath.endswith(".png"):
		return "image/png"

	elif RequestPath.endswith(".json"):
		return "application/json"

	elif RequestPath.endswith(".txt"):
		return "text/plain"

	return "text/html"

# Server main operational class.
class ServerClass(BaseHTTPRequestHandler):
	def SetResponse(self, ResponseCode, ContentType):
		self.send_response(ResponseCode)
		self.send_header("Content-type", ContentType)
		self.end_headers()

	def do_GET(self):
		ResponseContent = ReadGETParameters(self.path.lower())
		ContentType = SetContentType(self.path.lower())

		if ResponseContent == None:
			self.SetResponse(404, "text/html")
			ResponseContent = ReadGETParameters("/404.html").replace("[HTML:RequestPath]", self.path).encode("utf-8")
		else:
			self.SetResponse(200, ContentType)

		if ResponseContent != None:
			#self.wfile.write(str(ResponseContent).encode("utf-8"))
			self.wfile.write(ResponseContent)

# Main function running the server.
def RunServer():
	Server = HTTPServer(("", 9887), ServerClass)
	Logging("D", "Starting HTTP Server.")

	try:
		Server.serve_forever()

	except KeyboardInterrupt:
		Logging("D", "Stopping HTTP Server.")
		Server.server_close()

if  __name__ == "__main__":
	LoadConfig()
	if UserConfig["Standalone UI enabled [Refresh rate]"] == "" or UserConfig["Standalone UI enabled [Refresh rate]"] == None or UserConfig["Standalone UI enabled [Refresh rate]"] == False:
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