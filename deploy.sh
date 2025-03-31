#!/bin/bash

# CloudTrace Deployment Script
# This script sets up the CloudTrace application on a production server

# Exit on error
set -e

# Configuration variables
APP_DIR="$PWD"
LOG_DIR="/var/log/cloudtrace"
SERVICE_NAME="cloudtrace"
VENV_DIR="$APP_DIR/venv"

echo "=== CloudTrace Deployment ==="
echo "Deploying to: $APP_DIR"

# Create log directory if it doesn't exist
if [ ! -d "$LOG_DIR" ]; then
    echo "Creating log directory: $LOG_DIR"
    sudo mkdir -p $LOG_DIR
    sudo chown -R $(whoami):$(whoami) $LOG_DIR
fi

# Create virtual environment if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv $VENV_DIR
else
    echo "Using existing virtual environment at $VENV_DIR"
fi

# Activate virtual environment and install dependencies
echo "Installing dependencies..."
source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
deactivate

# Create data directory if it doesn't exist
if [ ! -d "$APP_DIR/data" ]; then
    echo "Creating data directory..."
    mkdir -p $APP_DIR/data
    chmod 755 $APP_DIR/data
fi

# Create the systemd service file
echo "Creating systemd service file..."
cat > /tmp/cloudtrace.service << EOF
[Unit]
Description=CloudTrace - Cloud Provider Benchmark Tool
After=network.target

[Service]
User=$(whoami)
WorkingDirectory=$APP_DIR
ExecStart=$VENV_DIR/bin/python $APP_DIR/app.py
Restart=always
RestartSec=10
StandardOutput=append:$LOG_DIR/stdout.log
StandardError=append:$LOG_DIR/stderr.log
Environment=PATH=$VENV_DIR/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
CapabilityBoundingSet=CAP_NET_RAW
AmbientCapabilities=CAP_NET_RAW

[Install]
WantedBy=multi-user.target
EOF

# Install the service file
echo "Installing systemd service..."
sudo mv /tmp/cloudtrace.service /etc/systemd/system/$SERVICE_NAME.service
sudo systemctl daemon-reload

# Configure Nginx as reverse proxy if installed
if command -v nginx &> /dev/null; then
    echo "Setting up Nginx reverse proxy..."
    cat > /tmp/cloudtrace_nginx << EOF
server {
    listen 80;
    server_name _;

    location /static {
        alias $APP_DIR/static;
        expires 30d;
    }

    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    sudo mv /tmp/cloudtrace_nginx /etc/nginx/sites-available/cloudtrace
    
    # Enable the site if it's not already enabled
    if [ ! -f /etc/nginx/sites-enabled/cloudtrace ]; then
        sudo ln -s /etc/nginx/sites-available/cloudtrace /etc/nginx/sites-enabled/
    fi
    
    # Test and reload nginx
    sudo nginx -t && sudo systemctl reload nginx
fi

# Restart the CloudTrace service
echo "Restarting CloudTrace service..."
sudo systemctl restart $SERVICE_NAME.service
sudo systemctl enable $SERVICE_NAME.service

# Check the service status
echo "Service status:"
sudo systemctl status $SERVICE_NAME.service --no-pager

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Access the application at:"
echo "  http://$(hostname -I | awk '{print $1}')/"
echo ""
echo "Check logs at:"
echo "  $LOG_DIR/stdout.log"
echo "  $LOG_DIR/stderr.log"
echo ""
echo "Service management commands:"
echo "  sudo systemctl status $SERVICE_NAME.service  # Check status"
echo "  sudo systemctl restart $SERVICE_NAME.service # Restart service"
echo "  sudo systemctl stop $SERVICE_NAME.service    # Stop service"
echo "  sudo journalctl -u $SERVICE_NAME.service     # View service logs" 