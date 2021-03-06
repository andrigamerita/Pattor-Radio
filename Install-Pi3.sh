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

sudo apt update

sudo apt install -y \
python3 \
sox libsox-fmt-mp3

cd Server/
mkdir Optional/ && cd Optional/
git clone https://github.com/mundeeplamport/PiFM.git

cd PiFM/
bash ./setup.sh