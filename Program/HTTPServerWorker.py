#!/usr/bin/python3

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

from http.server import BaseHTTPRequestHandler, HTTPServer
from sys import argv
from Helpers.LoggingHelper import *
from Helpers.LoadingHelper import *

def Test():
	return "Goodbye, world."

def ReadGETParameters(RequestPath):
	if RequestPath == "/" or RequestPath == "/index.html":
		WebUIMainFile = LoadFile("WebUI.html", "r")
		WebUIMain = WebUIMainFile.read()
		WebUIMainFile.close()
		return WebUIMain

	elif RequestPath == "/404.html":
		Error404File = LoadFile("404.html", "r")
		Error404 = Error404File.read()
		Error404File.close()
		return Error404

	elif RequestPath == "/?test":
		return Test()

	return None

class ServerClass(BaseHTTPRequestHandler):
	def SetResponse(self, ResponseCode):
		self.send_response(ResponseCode)
		self.send_header("Content-type", "text/html")
		self.end_headers()

	def do_GET(self):
		ResponseText = ReadGETParameters(self.path.lower())

		if ResponseText == None:
			self.SetResponse(404)
			ResponseText = ReadGETParameters("/404.html").replace("[RequestPath]", self.path)
		else:
			self.SetResponse(200)

		self.wfile.write(str(ResponseText).encode("utf-8"))

def RunServer():
	Server = HTTPServer(("", 9887), ServerClass)
	Logging("D", "Starting HTTP Server.")

	try:
		Server.serve_forever()

	except KeyboardInterrupt:
		Logging("D", "Stopping HTTP Server.")
		Server.server_close()

if  __name__ == "__main__":
	RunServer()