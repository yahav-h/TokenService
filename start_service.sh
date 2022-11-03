#!/bin/sh
source ./venv3/bin/activate
./venv3/bin/python3 -m pip install --upgrade pip && ./venv3/bin/python3 -m pip install -r ./requirements.txt
sudo nohup ./venv3/bin/python3 ./token_service_main.py &
