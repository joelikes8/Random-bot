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

# Function to upload a file to GitHub
def upload_file(file_path):
    try:
        # Get the file name
        file_name = os.path.basename(file_path)
        
        # Skip .git files and directories
        if '.git' in file_path or '__pycache__' in file_path or '.upm' in file_path or '.pythonlibs' in file_path or '.cache' in file_path or '.local' in file_path:
            print(f"Skipping {file_path}")
            return
        
        # Skip large binary files like generated-icon.png
        if file_name == 'generated-icon.png' or file_name == 'uv.lock':
            print(f"Skipping large binary file: {file_path}")
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

# Only upload the cogs directory
for root, dirs, files in os.walk('./cogs'):
    for file in files:
        if file.endswith('.py'):
            full_path = os.path.join(root, file)
            upload_file(full_path)

print("Upload of cogs directory complete!")
