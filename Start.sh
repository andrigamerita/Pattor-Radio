#!/bin/bash

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

ScriptPath=$(realpath $0)
ScriptDir=$(dirname $ScriptPath)
cd $ScriptDir

mkdir Data/ 2>/dev/null

python3 ./Program/HTTPServer.py & HTTPServerPID=$!
python3 ./Program/Radio.py

echo "[D] Killing the HTTPServer."
kill $HTTPServerPID