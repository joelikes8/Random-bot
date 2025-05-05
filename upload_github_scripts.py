import os
import base64
import requests
import json
import logging

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

def upload_file(file_path):
    try:
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Skip .git files and directories
        if '.git' in file_path or '__pycache__' in file_path or '.upm' in file_path or '.pythonlibs' in file_path or '.cache' in file_path or '.local' in file_path:
            logger.info(f"Skipping {file_path}")
            return
        
        # Skip large binary files like generated-icon.png
        if file_name == 'generated-icon.png' or file_name == 'uv.lock':
            logger.info(f"Skipping large binary file: {file_path}")
            return
        
        # Read file content
        with open(file_path, 'rb') as file:
            content = file.read()
            
        # Determine the GitHub path (relative to repo root)
        github_path = file_path
        if github_path.startswith('./') or github_path.startswith('/'):
            github_path = github_path[2:] if github_path.startswith('./') else github_path[1:]
        
        # Encode content to base64
        content_encoded = base64.b64encode(content).decode('utf-8')
        
        # Create the API request data
        data = {
            'message': f'Upload {file_name}',
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

# GitHub-related scripts to upload
github_files = [
    'github_check_repo.py',
    'github_upload.py',
    'upload_new_files.py',
    'upload_specific_files.py',
    'upload_github_scripts.py'  # Upload this file itself
]

if __name__ == "__main__":
    logger.info("Starting upload of GitHub scripts...")
    
    for file in github_files:
        if os.path.exists(file):
            upload_file(file)
        else:
            logger.warning(f"File {file} does not exist, skipping")
    
    logger.info("Finished uploading GitHub scripts")
