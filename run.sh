#!/bin/bash

# Define the path to the Python script
python_script="/root/PisoWifi/coin_slot.py"

# Define the path to the virtual environment
env_path="/root/PisoWifi/"

# Activate the virtual environment
source "$env_path/bin/activate"

# Run the Python script using the activated environment
/usr/bin/python3 "$python_script"