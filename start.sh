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

cd Program/
python3 ./HTTPServerWorker.py &

cd ..
python3 ./Program/Radio.py