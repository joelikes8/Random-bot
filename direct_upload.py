import os
import base64
import requests
import json

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

# Function to upload a specific file
def upload_file(file_path):
    try:
        # Read file content
        with open(file_path, 'rb') as file:
            content = file.read()
        
        # Determine the GitHub path
        github_path = file_path
        
        # Encode content to base64
        content_encoded = base64.b64encode(content).decode('utf-8')
        
        # Create the API request data
        data = {
            'message': f'Update {file_path}',
            'content': content_encoded
        }
        
        # Check if file already exists
        check_url = f'{API_URL}/{github_path}'
        check_response = requests.get(check_url, headers=headers)
        
        if check_response.status_code == 200:
            # File exists, update it
            file_data = check_response.json()
            data['sha'] = file_data['sha']
            print(f"Updating existing file: {file_path}")
        else:
            print(f"Creating new file: {file_path}")
        
        # Make the API request
        response = requests.put(f'{API_URL}/{github_path}', headers=headers, data=json.dumps(data))
        
        # Check response
        if response.status_code in [200, 201]:
            print(f"Successfully uploaded {file_path}")
            return True
        else:
            print(f"Failed to upload {file_path}: {response.status_code} {response.text}")
            return False
    
    except Exception as e:
        print(f"Error uploading {file_path}: {str(e)}")
        return False

# Upload critical files
files_to_upload = [
    'utils/render_config.py',
    'utils/roblox_api.py',
    'cogs/verification.py'
]

for file_path in files_to_upload:
    upload_file(file_path)
