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
from Helpers.LoadingHelper import *

def Test():
	return "<p>Goodbye, world.</p>"

# Reading contents of a text file
def TextFileRead(FilePath):
	File = LoadFile(FilePath, "r")

	if File == None:
		return None

	FileContent = File.read()
	File.close()

	return FileContent

# Patching the Base HTML file with the specific page template desired
def PatchHTML(TemplateFilePath):
	TemplateFile = LoadFile(TemplateFilePath, "r")

	if TemplateFile == None:
		return None

	TemplateContent = TemplateFile.read()
	TemplateFile.close()

	PatchedHTML = BaseHTML.replace("[HTML:BodyMain]", TemplateContent)

	try:
		if WebUITitles[basename(TemplateFilePath).replace(".html", "")] == None:
			return PatchedHTML.replace("[HTML:Title]", "")
		else:
			return PatchedHTML.replace("[HTML:Title]", WebUITitles[basename(TemplateFilePath).replace(".html", "")])
	except:
		return PatchedHTML

# Writing playing directions to file for the main program to read
def WritePlayDirections(PlayDirection):
	PlayDirectionsFile = LoadFile("Data/PlayDirections", "w")

	if PlayDirectionsFile != None:
		if PlayDirection == "Skip":
			PlayDirectionsFile.write("Skip")

	PlayDirectionsFile.close()

	return None

# Reading GET requests and responding accordingly
def ReadGETParameters(RequestPath):
	if RequestPath == "/" or RequestPath == "/index.html":
		return PatchHTML("Program/WebUI/Templates/Main.html")

	elif RequestPath == "/404" or RequestPath == "/404.html":
		return PatchHTML("Program/WebUI/Templates/404.html")

	elif RequestPath == "/?Action=SkipSongs".lower():
		return TextFileRead("Program/WebUI/Forms/SkipSongs.html")

	elif RequestPath.startswith("/?RunAction=SkipSongs".lower()):
		WritePlayDirections("Skip")
		return TextFileRead("Program/WebUI/Forms/SkipSongs.html")

	return None
	#return "[HTML:Error404]"

# Server main operational class
class ServerClass(BaseHTTPRequestHandler):
	def SetResponse(self, ResponseCode):
		self.send_response(ResponseCode)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):
		ResponseText = ReadGETParameters(self.path.lower())

		if ResponseText == None: #"[HTML:Error404]":
			self.SetResponse(404)
			ResponseText = ReadGETParameters("/404.html").replace("[HTML:RequestPath]", self.path)
		else:
			self.SetResponse(200)

		if ResponseText != None:
			self.wfile.write(str(ResponseText).encode("utf-8"))

# Main function running the server
def RunServer():
	Server = HTTPServer(("", 9887), ServerClass)
	Logging("D", "Starting HTTP Server.")

	try:
		Server.serve_forever()

	except KeyboardInterrupt:
		Logging("D", "Stopping HTTP Server.")
		Server.server_close()

if  __name__ == "__main__":
	BaseHTMLFile = LoadFile("Program/WebUI/Base.html", "r")

	if BaseHTMLFile == None:
		Logging("D", "Couldn't load Base HTML File. WebUI might be broken.")
		BaseHTML = "[HTML:BodyMain]"
	else:
		BaseHTML = BaseHTMLFile.read()
		BaseHTMLFile.close()

	WebUITitlesFile = LoadFile("Program/WebUI/Titles.config", "r")

	if WebUITitlesFile == None:
		Logging("D", "Couldn't load WebUI Titles File. WebUI might be broken.")
	else:
		WebUITitles = json.load(WebUITitlesFile)
		WebUITitlesFile.close()

	RunServer()