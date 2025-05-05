import os
import base64
import requests
import json
import logging
import time
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

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

def upload_file(file_path, commit_message=None):
    try:
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Skip .git files, sensitive config files, and large binary files
        if '.git' in file_path or '__pycache__' in file_path or '.upm' in file_path or '.pythonlibs' in file_path:
            logger.info(f"Skipping system file: {file_path}")
            return False
            
        # Skip sensitive files or large binary files
        if file_path == '.env' or file_name == 'generated-icon.png' or file_name == 'uv.lock':
            logger.info(f"Skipping sensitive or large file: {file_path}")
            return False
        
        # Read file content
        with open(file_path, 'rb') as file:
            content = file.read()
            
        # Determine the GitHub path (relative to repo root)
        github_path = file_path
        if github_path.startswith('./') or github_path.startswith('/'):
            github_path = github_path[2:] if github_path.startswith('./') else github_path[1:]
        
        # Encode content to base64
        content_encoded = base64.b64encode(content).decode('utf-8')
        
        # Default commit message if none provided
        if not commit_message:
            commit_message = f'Update {file_name} - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        
        # Create the API request data
        data = {
            'message': commit_message,
            'content': content_encoded
        }
        
        # Check if file already exists
        check_url = f'{API_URL}/{github_path}'
        check_response = requests.get(check_url, headers=headers)
        
        if check_response.status_code == 200:
            # File exists, update it
            file_data = check_response.json()
            data['sha'] = file_data['sha']
            logger.info(f"Updating existing file: {file_path}")
        else:
            logger.info(f"Creating new file: {file_path}")
        
        # Make the API request
        response = requests.put(f'{API_URL}/{github_path}', headers=headers, data=json.dumps(data))
        
        # Check response
        if response.status_code in [200, 201]:
            logger.info(f"Successfully uploaded {file_path}")
            return True
        else:
            logger.error(f"Failed to upload {file_path}: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error uploading {file_path}: {str(e)}")
        return False

def get_modified_files(minutes=10):
    """Get files modified in the last X minutes"""
    current_time = time.time()
    modified_files = []
    
    # Walk through the directory
    for root, dirs, files in os.walk('.'):
        # Skip hidden directories and files
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        
        for file in files:
            file_path = os.path.join(root, file)
            
            # Skip certain files
            if file.startswith('.') or '__pycache__' in file_path:
                continue
                
            # Get file modification time
            try:
                mtime = os.path.getmtime(file_path)
                if (current_time - mtime) <= (minutes * 60):
                    modified_files.append(file_path)
            except Exception as e:
                logger.error(f"Error checking file {file_path}: {str(e)}")
    
    return modified_files

def sync_recent_changes(minutes=10):
    """Sync recently modified files to GitHub"""
    logger.info(f"Checking for files modified in the last {minutes} minutes...")
    
    # Get recently modified files
    modified_files = get_modified_files(minutes)
    
    if not modified_files:
        logger.info("No recently modified files found.")
        return 0
    
    logger.info(f"Found {len(modified_files)} recently modified files to upload.")
    
    # Upload each file
    success_count = 0
    for file_path in modified_files:
        if upload_file(file_path):
            success_count += 1
    
    logger.info(f"Successfully uploaded {success_count} of {len(modified_files)} files.")
    return success_count

# Also upload this script itself
def upload_self():
    current_file = os.path.basename(__file__)
    logger.info(f"Uploading this script ({current_file}) to GitHub...")
    upload_file(current_file, f"Add auto GitHub sync script - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    # Check if GITHUB_TOKEN is set
    if not GITHUB_TOKEN:
        logger.error("Missing GITHUB_TOKEN environment variable. Cannot upload to GitHub.")
    else:
        logger.info("Starting GitHub sync...")
        sync_recent_changes(60)  # Check files modified in the last 60 minutes
        upload_self()
        logger.info("GitHub sync completed.")
