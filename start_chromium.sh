#!/bin/bash
# Wait for 10 seconds to ensure the Dash app is up and running
sleep 10
# Set the DISPLAY environment variable and start Chromium in kiosk mode
export DISPLAY=:0
/usr/bin/chromium-browser --kiosk http://localhost:8050
