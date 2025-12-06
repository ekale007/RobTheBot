#!/bin/bash
# Installation script for Robot Arm Control System

echo "Installing Robot Arm Control System..."

# Update system
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and pip
sudo apt-get install -y python3 python3-pip python3-venv

# Create project directory
mkdir -p ~/robot-arm-control
cd ~/robot-arm-control

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
mkdir -p templates static data logs

# Make scripts executable
chmod +x app.py

# Create systemd service
sudo tee /etc/systemd/system/robot-arm.service > /dev/null <<EOF
[Unit]
Description=Robot Arm Control System
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/$USER/robot-arm-control
ExecStart=/home/$USER/robot-arm-control/venv/bin/python app.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable robot-arm.service
sudo systemctl start robot-arm.service

echo "Installation complete!"
echo "Access the control panel at: http://$(hostname -I | awk '{print $1}'):5000"
echo "Check status with: sudo systemctl status robot-arm"