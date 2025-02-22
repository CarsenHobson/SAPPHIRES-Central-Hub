#!/usr/bin/env python3
import os
import subprocess

# Set the DISPLAY environment variable to :0
os.environ['DISPLAY'] = ':0'

# Run unclutter with the desired options
subprocess.run(['unclutter', '-idle', '0', '-root'])
