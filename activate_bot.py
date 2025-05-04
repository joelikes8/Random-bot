import os
import logging
import threading
import time
from dotenv import load_dotenv
from bot import bot

# Set up logging
logging.basicConfig(level=logging.INFO,
                  format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Get Discord token
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

def start_bot():
    if not DISCORD_TOKEN:
        logger.error("Missing DISCORD_TOKEN environment variable")
        return
    
    logger.info("Starting Discord bot from web server context")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")

# Start the bot in a background thread when this module is imported
bot_thread = threading.Thread(target=start_bot)
bot_thread.daemon = True
bot_thread.start()

# Export a function that we can call to check if the bot is running
def is_bot_running():
    return bot_thread.is_alive()
