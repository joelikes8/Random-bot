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

# Upload the .env.example file
upload_file('.env.example')

# Create and upload a requirements.txt file
requirements_content = """aiohttp==3.9.5
discord.py==2.3.2
email-validator==2.1.0.post1
flask==3.0.2
flask-login==0.6.3
flask-sqlalchemy==3.1.1
gunicorn==23.0.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
requests==2.32.3
trafilatura==1.7.0
"""

# Encode requirements content
requirements_encoded = base64.b64encode(requirements_content.encode()).decode('utf-8')

# Create requirements.txt using GitHub API
data = {
    'message': 'Add requirements.txt',
    'content': requirements_encoded
}

# Check if file already exists
check_url = f'{API_URL}/requirements.txt'
check_response = requests.get(check_url, headers=headers)

if check_response.status_code == 200:
    # File exists, update it
    file_data = check_response.json()
    data['sha'] = file_data['sha']
    print("Updating existing file: requirements.txt")
else:
    print("Creating new file: requirements.txt")

# Make the API request
response = requests.put(f'{API_URL}/requirements.txt', headers=headers, data=json.dumps(data))

# Check response
if response.status_code in [200, 201]:
    print("Successfully uploaded requirements.txt")
else:
    print(f"Failed to upload requirements.txt: {response.status_code} {response.text}")

print("Upload of additional files complete!")
