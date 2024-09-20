#!/bin/bash

echo "Starting spoofer.py with PM2..."
pm2 start spoofer.py --interpreter python3

echo "Starting Oxapay webhook with PM2..."
pm2 start "python3 -m gunicorn --workers 3 --bind 0.0.0.0:5000 oxapay.webhook:app" --name "oxapay-webhook"

pm2 list

echo "All services started successfully."
