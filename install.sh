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

#PYTHONPATH=$(dirname $SCRIPTDIR)/PythonPath
#export PYTHONPATH=$PYTHONPATH

sudo apt update

sudo apt install \
python3 python3-pip \
sox libsox-fmt-mp3

#mkdir requirements/
#cd requirements/
#wget --no-check-certificate "https://files.pythonhosted.org/packages/16/b3/f7aa8edf2ff4495116f95fd442b2a346aa55d1d46313143c8814886dbcdb/mutagen-1.45.1-py3-none-any.whl"
#wget --no-check-certificate "https://files.pythonhosted.org/packages/fd/1d/e9579cf5cbc3d85e12d04b2b2d0664d87ca132712baf9bc78bf6160bd554/pydeck-0.6.0-py2.py3-none-any.whl"
#wget --no-check-certificate "https://files.pythonhosted.org/packages/b2/97/ae3c52932853399cc748e4f3e4947659b0b487fad3a4df391557442a92db/streamlit-0.76.0-py2.py3-none-any.whl
#wget --no-check-certificate "https://files.pythonhosted.org/packages/7d/cc/e8908bbb2921732f6851ebbbe4b77b925aab62e644ab9402f21c84fa6107/ipykernel-5.4.3-py3-none-any.whl"
#wget --no-check-certificate ""

#sudo -H pip3 install --target=$PYTHONPATH "mutagen-1.45.1-py3-none-any.whl"
#sudo -H pip3 install --target=$PYTHONPATH "pydeck-0.6.0-py2.py3-none-any.whl"
#sudo -H pip3 install --target=$PYTHONPATH "streamlit-0.76.0-py2.py3-none-any.whl"
#sudo -H pip3 install --target=$PYTHONPATH "ipykernel-5.4.3-py3-none-any.whl"
#sudo -H pip3 install --target=$PYTHONPATH ""

cd ..
rm -rf requirements/

cd Program/PiFM/
bash ./setup.sh
