#!/bin/bash

# Update package manager
apt-get update
apt-get upgrade

# Install packages
sudo apt-get install python3-pip python-smbus python3-dev i2c-tools

# Install Python packages using pip
pip3 install requests
pip3 install OPi.GPIO
pip3 install ping3

# Check if overlays already exist in armbianEnv.txt
if grep -q "overlays=" /boot/armbianEnv.txt; then
  # Replace the value of the overlays parameter
  sudo sed -i "s/^overlays=.*/overlays=i2c0 i2c1/" /boot/armbianEnv.txt
else
  # Add overlays parameter to armbianEnv.txt
  echo "overlays=i2c0 i2c1" | sudo tee -a /boot/armbianEnv.txt
fi

# Check if i2c-dev module is already in /etc/modules
if ! grep -q "^i2c-dev$" /etc/modules; then
  # Add i2c-dev module to /etc/modules
  echo "i2c-dev" | sudo tee -a /etc/modules
fi

# Clone Git repository
# git clone https://github.com/tunitz/PisoWifi.git

chmod +x coin_slot.py

# Define the path to the startup script
startup_script="/root/PisoWifi/coin_slot.py"

# Check if the startup script is already in the rc.local file
if grep -q "$startup_script" /etc/rc.local; then
    echo "Startup script already exists in rc.local"
else
    # Add the startup script to the rc.local file
    sed -i "/exit 0/d" /etc/rc.local
    echo "$startup_script &" >> /etc/rc.local
    echo "exit 0" >> /etc/rc.local
    echo "Startup script added to rc.local"
fi

sudo reboot