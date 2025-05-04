import os
import logging
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

if not DISCORD_TOKEN:
    logger.error("Missing DISCORD_TOKEN environment variable")
    exit(1)

def main():
    logger.info("Starting Discord bot")
    try:
        bot.run(DISCORD_TOKEN)
    except Exception as e:
        logger.error(f"Error running Discord bot: {e}")
        
if __name__ == "__main__":
    main()
