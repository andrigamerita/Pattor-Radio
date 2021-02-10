#!/bin/bash

# -
# | Pattor Radio
# | PiFM-powered pirate radio
# | on the Raspberry Pi, with goodies
# |
# | Copyright (C) 2021, OctoSpacc
# | Licensed under the GPLv3
# -

SCRIPTPATH=$(realpath $0)
SCRIPTDIR=$(dirname $SCRIPTPATH)
cd $SCRIPTDIR

python3 ./Program/Radio.py
