import os
import asyncio
import logging
import time
import threading
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Import login functionality
from login_roblox import update_cookie_in_env, join_group_with_credentials

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# USMC Group ID
GROUP_ID = '11966964'

# Check if we're running on Render
RUNNING_ON_RENDER = 'RENDER' in os.environ

# Cookie refresh interval (6 hours)
COOKIE_REFRESH_INTERVAL = 6 * 60 * 60

# Last refresh time
last_refresh_time = 0

async def perform_roblox_login():
    """
    Perform Roblox login and update the environment variables
    """
    logger.info("Starting automatic Roblox login process...")
    
    # Try to update the cookie in environment variables
    cookie_success, cookie_message = await update_cookie_in_env()
    
    if cookie_success:
        logger.info(f"Successfully updated Roblox cookie: {cookie_message}")
        
        # Try to join the USMC group
        logger.info(f"Attempting to join Roblox group {GROUP_ID}...")
        group_success, group_message = await join_group_with_credentials(GROUP_ID)
        
        if group_success:
            logger.info(f"Successfully joined USMC group: {group_message}")
            return True
        else:
            logger.warning(f"Failed to join USMC group: {group_message}")
            # Still consider this a success if we got the cookie
            return True
    else:
        logger.error(f"Failed to update Roblox cookie: {cookie_message}")
        return False

def update_github_env():
    """
    Update GitHub repository with the new environment variables
    """
    try:
        # Only update GitHub if we have a token
        if not os.environ.get('GITHUB_TOKEN'):
            logger.warning("Missing GITHUB_TOKEN environment variable, skipping GitHub update")
            return False
            
        # Import the GitHub cookie updater
        import github_update_cookie
        github_update_cookie.main()
        logger.info("Successfully updated GitHub repository with new environment variables")
        return True
    except Exception as e:
        logger.error(f"Failed to update GitHub repository: {e}")
        return False

async def refresh_cookie():
    """
    Refresh the Roblox cookie periodically
    """
    global last_refresh_time
    
    # Get current time
    current_time = time.time()
    
    # Check if we need to refresh the cookie
    if current_time - last_refresh_time > COOKIE_REFRESH_INTERVAL:
        logger.info("Cookie refresh interval reached, refreshing Roblox cookie...")
        
        # Perform Roblox login
        login_success = await perform_roblox_login()
        
        if login_success:
            # Update the last refresh time
            last_refresh_time = current_time
            logger.info(f"Roblox cookie refreshed successfully. Next refresh in {COOKIE_REFRESH_INTERVAL//3600} hours")
            
            # Update GitHub repository if needed
            if RUNNING_ON_RENDER:
                update_github_env()
        else:
            logger.error("Failed to refresh Roblox cookie")

async def cookie_refresh_loop():
    """
    Background loop to periodically refresh the Roblox cookie
    """
    while True:
        try:
            await refresh_cookie()
        except Exception as e:
            logger.error(f"Error in cookie refresh loop: {e}")
        
        # Wait for a while before checking again (every 15 minutes)
        await asyncio.sleep(15 * 60)

def start_cookie_refresh_thread():
    """
    Start a background thread to refresh the Roblox cookie
    """
    # Create an event loop in the thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Wait a few seconds before starting to allow other initialization to complete
    time.sleep(5)
    
    # First do an initial login
    logger.info("Performing initial Roblox login in background thread...")
    login_success = loop.run_until_complete(perform_roblox_login())
    
    if login_success:
        logger.info("Initial Roblox login successful, updating GitHub repository...")
        # Update GitHub with the new cookie
        update_github_env()
    
    # Then start the refresh loop
    logger.info("Starting cookie refresh loop...")
    loop.run_until_complete(cookie_refresh_loop())

# Start the cookie refresh thread (only if running on Render)
if RUNNING_ON_RENDER:
    logger.info("Starting Roblox cookie refresh thread for Render environment")
    cookie_thread = threading.Thread(target=start_cookie_refresh_thread)
    cookie_thread.daemon = True
    cookie_thread.start()
else:
    logger.info("Not running on Render, skipping automatic Roblox login")
