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

sudo apt update

sudo apt install -y \
python3 \
sox libsox-fmt-mp3

cd Program/
mkdir Optional/ && cd Optional/
git clone https://github.com/mundeeplamport/PiFM.git

cd PiFM/
bash ./setup.sh