#!/bin/bash

# -
# | Pattor Radio
# | Goodies-packed pirate radio station on Linux
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the AGPLv3
# -

SCRIPTPATH=$(realpath $0)
SCRIPTDIR=$(dirname $SCRIPTPATH)
cd $SCRIPTDIR

mkdir Data/

python3 ./Program/HTTPServer.py & HTTPSERVERWORKERPID=$!
python3 ./Program/Radio.py

#sleep 1
echo "[D] Killing the HTTPServerWorker."
kill $HTTPSERVERWORKERPID