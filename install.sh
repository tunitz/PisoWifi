#!/bin/bash

# Update package manager
apt-get update
apt-get upgrade

# Install packages
sudo apt-get install python3-pip python-smbus python3-dev i2c-tools

# Install Python packages using pip
pip3 install requests OPi.GPIO i2clcd

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

chmod +x main.py

# Set the file name and path
file_path="/lib/systemd/system/main.service"

# Set the Python script path
script_path="/root/PisoWifi/main.py"

# Set the Python script parent path
script_parent_path="/root/PisoWifi"

# Check if the file already exists
if [ -f "$file_path" ]; then
  echo "Service file already exists"
else
  # Write the file contents
  echo "[Unit]" > $file_path
  echo "Description=My Coin Slot Service" >> $file_path
  echo "After=multi-user.target" >> $file_path
  echo "" >> $file_path
  echo "[Service]" >> $file_path
  echo "Type=simple" >> $file_path
  echo "WorkingDirectory=$script_parent_path" >> $file_path
  echo "Environment=PYTHONOATH=$script_parent_path" >> $file_path
  echo "Restart=always" >> $file_path
  echo "ExecStart=/usr/bin/python3 $script_path" >> $file_path
  echo "" >> $file_path
  echo "[Install]" >> $file_path
  echo "WantedBy=multi-user.target" >> $file_path

fi

sudo chmod 644 $file_path

sudo systemctl daemon-reload
sudo systemctl enable main.service

sudo reboot