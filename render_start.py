# Special startup file for Render.com deployment

import os
import sys
import logging
import asyncio
import threading

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# This script sets up environment variables and special configurations for Render.com
logger.info("Starting Render.com specific configuration")

# Set environment variable to identify Render environment
os.environ['RENDER'] = 'true'

# First, run Roblox login before starting the main application
logger.info("Performing initial Roblox login to setup authentication")

# Run a one-time Roblox login to get a fresh cookie
from login_roblox import update_cookie_in_env

def run_initial_login():
    # Create an event loop for the async login function
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        success, message = loop.run_until_complete(update_cookie_in_env())
        
        if success:
            logger.info(f"Initial Roblox login successful: {message}")
        else:
            logger.warning(f"Initial Roblox login failed: {message}")
            logger.warning("Bot will still start, but verification might not work correctly")
    except Exception as e:
        logger.error(f"Error during initial Roblox login: {e}")
        logger.warning("Continuing with bot startup despite login error")

# Run the initial login in a separate thread to avoid blocking startup
login_thread = threading.Thread(target=run_initial_login)
login_thread.daemon = True
login_thread.start()

# Import the auto-login module to start the background refresh
logger.info("Setting up automatic Roblox cookie refresh")
import auto_login_roblox

# Import the main application
logger.info("Importing main application")
from main import app

logger.info("Starting Gunicorn server with Render-specific configurations")

# The app variable is imported by Gunicorn from this file
# Use the following command in Render.com:  
# gunicorn --bind 0.0.0.0:$PORT --workers 1 render_start:app