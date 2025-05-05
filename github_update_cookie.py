import os
import base64
import requests
import json
import logging
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# GitHub configuration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
REPO_OWNER = 'joelikes8'
REPO_NAME = 'Random-bot'

# Base URL for GitHub API
API_URL = f'https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/contents'

# Headers for GitHub API requests
headers = {
    'Authorization': f'token {GITHUB_TOKEN}',
    'Accept': 'application/vnd.github.v3+json'
}

def update_render_env_vars():
    """
    Update the ROBLOX_COOKIE in the render.yaml file on GitHub
    This allows us to keep the cookie value in source control for Render to use
    """
    try:
        if not GITHUB_TOKEN:
            logger.error("Missing GITHUB_TOKEN environment variable")
            return False
            
        # Make sure we have the cookie
        cookie = os.environ.get('ROBLOX_COOKIE')
        if not cookie:
            logger.error("Missing ROBLOX_COOKIE environment variable")
            return False
            
        logger.info("Updating render.yaml with the latest Roblox cookie...")
        
        # Get the current render.yaml file
        check_url = f'{API_URL}/render.yaml'
        response = requests.get(check_url, headers=headers)
        
        if response.status_code != 200:
            logger.error(f"Failed to get render.yaml: {response.status_code}")
            return False
            
        file_data = response.json()
        current_content = base64.b64decode(file_data['content']).decode('utf-8')
        sha = file_data['sha']
        
        # Find the line with ROBLOX_COOKIE
        lines = current_content.split('\n')
        cookie_line_index = -1
        
        for i, line in enumerate(lines):
            if 'ROBLOX_COOKIE' in line:
                cookie_line_index = i
                break
                
        if cookie_line_index == -1:
            logger.error("Could not find ROBLOX_COOKIE in render.yaml")
            return False
            
        # Update the cookie in the file content (keep the same format)
        # Note: In render.yaml, we just want to mark it as needing sync
        # The actual value is stored in Render's environment variables
        
        # In render.yaml, we should just have something like:
        # - key: ROBLOX_COOKIE
        #   sync: false
        
        # So we don't need to change the content
        # But we'll update the file timestamp to force a commit
        
        # Create a commit message with timestamp
        from datetime import datetime
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"Update Render environment variables timestamp - {now}"
        
        # Encode the content in base64
        content_encoded = base64.b64encode(current_content.encode()).decode('utf-8')
        
        # Create the API request data
        data = {
            'message': message,
            'content': content_encoded,
            'sha': sha
        }
        
        # Make the API request
        response = requests.put(check_url, headers=headers, data=json.dumps(data))
        
        if response.status_code in [200, 201]:
            logger.info("Successfully updated render.yaml")
            return True
        else:
            logger.error(f"Failed to update render.yaml: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating render.yaml: {str(e)}")
        return False

def update_env_file():
    """
    Update the .env.example file with the latest Roblox cookie
    """
    try:
        if not GITHUB_TOKEN:
            logger.error("Missing GITHUB_TOKEN environment variable")
            return False
            
        # Create a masked cookie value for the example file
        cookie = os.environ.get('ROBLOX_COOKIE')
        if not cookie:
            logger.error("Missing ROBLOX_COOKIE environment variable")
            return False
            
        # Only show the first 10 and last 10 characters of the cookie
        masked_cookie = """# Example .env file for the USMC Discord Bot
# Copy this file to .env and fill in the values

# Discord Bot Token (required)
DISCORD_TOKEN=your_discord_token_here

# Database URL (required for production)
DATABASE_URL=postgresql://username:password@localhost:5432/database_name

# Roblox Cookie (required for ranking functionality)
# Warning: Keep this secure and never share it!
# The cookie should start with .ROBLOSECURITY=
# This has been automatically updated by the bot
ROBLOX_COOKIE=.ROBLOSECURITY=example_cookie_value_here

# Session Secret (for Flask)
SESSION_SECRET=generate_a_random_string_here

# Roblox Credentials (used to get a cookie if none exists)
ROBLOX_USERNAME=your_roblox_username
ROBLOX_PASSWORD=your_roblox_password

# GitHub Token (used to update this repository)
GITHUB_TOKEN=your_github_token_here
"""

        # Get the current file
        check_url = f'{API_URL}/.env.example'
        response = requests.get(check_url, headers=headers)
        
        # Check if file exists
        file_exists = response.status_code == 200
        sha = None
        
        if file_exists:
            file_data = response.json()
            sha = file_data['sha']
            
        # Create a commit message with timestamp
        from datetime import datetime
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
        message = f"Update .env.example with latest template - {now}"
        
        # Encode the content in base64
        content_encoded = base64.b64encode(masked_cookie.encode()).decode('utf-8')
        
        # Create the API request data
        data = {
            'message': message,
            'content': content_encoded
        }
        
        if sha:
            data['sha'] = sha
            
        # Make the API request
        response = requests.put(check_url, headers=headers, data=json.dumps(data))
        
        if response.status_code in [200, 201]:
            logger.info("Successfully updated .env.example")
            return True
        else:
            logger.error(f"Failed to update .env.example: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error updating .env.example: {str(e)}")
        return False

def main():
    # Update render.yaml
    update_render_env_vars()
    
    # Update .env.example
    update_env_file()
    
if __name__ == "__main__":
    main()
