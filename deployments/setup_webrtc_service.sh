#!/bin/bash

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "Please run as root"
    exit 1
fi

# Get the absolute path to the project directory
PROJECT_DIR=$(realpath $(dirname $(dirname $0)))

# Get the Python executable path
PYTHON_PATH=$(which python3)

# Get the current user
CURRENT_USER=$SUDO_USER
if [ -z "$CURRENT_USER" ]; then
    CURRENT_USER=$(whoami)
fi

# Create log files
touch /var/log/memory-webrtc.log
touch /var/log/memory-webrtc.error.log
chown $CURRENT_USER:$CURRENT_USER /var/log/memory-webrtc.log
chown $CURRENT_USER:$CURRENT_USER /var/log/memory-webrtc.error.log

# Check if .env file exists
ENV_FILE="$PROJECT_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    # If .env doesn't exist but .env.example does, copy it
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$ENV_FILE"
    else
        # Create new .env file
        touch "$ENV_FILE"
    fi
fi

# Ensure .env file has correct permissions
chown $CURRENT_USER:$CURRENT_USER "$ENV_FILE"
chmod 600 "$ENV_FILE"

# Check if OPENAI_API_KEY exists in .env
if ! grep -q "^OPENAI_API_KEY=" "$ENV_FILE"; then
    # Prompt for OpenAI API key if not in .env
    read -p "Enter your OpenAI API key: " OPENAI_API_KEY
    echo "OPENAI_API_KEY=$OPENAI_API_KEY" >> "$ENV_FILE"
    echo "Added OpenAI API key to .env file"
else
    echo "OpenAI API key already exists in .env file"
fi

# Create and configure the service file
cat > /etc/systemd/system/memory-webrtc.service << EOL
[Unit]
Description=Memory Query WebRTC Server
After=network.target

[Service]
Type=simple
User=$CURRENT_USER
Group=$CURRENT_USER
WorkingDirectory=$PROJECT_DIR
Environment=PYTHONPATH=$PROJECT_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$PYTHON_PATH $PROJECT_DIR/examples/memory_query.py server --host 0.0.0.0 --port 8765
Restart=always
RestartSec=3
StandardOutput=append:/var/log/memory-webrtc.log
StandardError=append:/var/log/memory-webrtc.error.log

[Install]
WantedBy=multi-user.target
EOL

# Reload systemd daemon
systemctl daemon-reload

# Enable and start the service
systemctl enable memory-webrtc
systemctl start memory-webrtc

echo "Memory WebRTC service has been installed and started!"
echo "To check the status: systemctl status memory-webrtc"
echo "To view logs: tail -f /var/log/memory-webrtc.log"
echo "To view error logs: tail -f /var/log/memory-webrtc.error.log"
echo "Environment file location: $ENV_FILE" 