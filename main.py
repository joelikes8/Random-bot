import logging
import os
import threading
import time
from dotenv import load_dotenv
from app import app

# Set up logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Import the bot activation module
# This will start the bot in a background thread
import activate_bot

# Add a route to check bot status
@app.route('/bot-status')
def bot_status():
    if activate_bot.is_bot_running():
        return {"status": "online"}, 200
    else:
        return {"status": "offline"}, 503

# This is needed for Gunicorn to find the Flask app
if __name__ == "__main__":
    # This will be used when running directly (not through gunicorn)
    logger.info("Starting web server")
    app.run(host="0.0.0.0", port=5000)
