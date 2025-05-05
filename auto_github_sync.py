import os
import base64
import requests
import json
import time
from datetime import datetime, timedelta
import subprocess

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
    """Upload a file to GitHub"""
    try:
        # Skip binary files and large files
        if file_path.endswith(('.png', '.jpg', '.jpeg', '.ico', '.gif', '.lock')) or \
           os.path.getsize(file_path) > 1000000:
            print(f"Skipping large or binary file: {file_path}")
            return False
           
        # Skip hidden files/directories except for important config files
        if ('/.' in file_path or file_path.startswith('.')) and \
           not file_path in ['.replit', '.env.example', '.render_config.py']:
            print(f"Skipping hidden file: {file_path}")
            return False
        
        # Skip non-project files
        if not file_path.endswith(('.py', '.md', '.yaml', '.yml', '.txt', '.json', '.env.example')):
            print(f"Skipping non-project file: {file_path}")
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
        
        # Create the API request data
        if commit_message is None:
            commit_message = f'Update {file_path} - Auto sync'
            
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

def get_modified_files(minutes=10):
    """Get files modified in the last X minutes"""
    modified_files = []
    cutoff_time = datetime.now() - timedelta(minutes=minutes)
    cutoff_timestamp = cutoff_time.timestamp()
    
    # Use find command to get modified files
    try:
        # More efficient find command that filters directly by file extension
        command = (
            f'find . -type f '
            f'\( -name "*.py" -o -name "*.md" -o -name "*.yaml" -o -name "*.yml" '
            f'-o -name "*.txt" -o -name "*.json" -o -name ".env.example" -o -name ".replit" \) '
            f'-not -path "*/.git/*" -not -path "*/__pycache__/*" -not -path "*/.cache/*" '
            f'-not -path "*/.local/*" -not -path "*/.upm/*" -mmin -{minutes}'
        )
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        files = result.stdout.strip().split('\n')
        
        # Filter out empty lines and any remaining unwanted files
        for file in files:
            if file and os.path.isfile(file) and os.path.getsize(file) <= 1000000:
                modified_files.append(file)
    except Exception as e:
        print(f"Error getting modified files: {str(e)}")
    
    return modified_files

def sync_recent_changes(minutes=10):
    """Sync recently modified files to GitHub"""
    files = get_modified_files(minutes)
    print(f"Found {len(files)} recently modified files")
    
    uploaded_count = 0
    for file in files:
        try:
            success = upload_file(file)
            if success:
                uploaded_count += 1
            # Add a small delay to avoid rate limiting
            time.sleep(0.5)
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
    
    print(f"Uploaded {uploaded_count} files to GitHub")
    return uploaded_count
    
def upload_self():
    """Upload this script itself"""
    return upload_file('auto_github_sync.py', 'Update auto-sync script')

# If this script is run directly
if __name__ == "__main__":
    print("===== Starting GitHub Auto-Sync =====")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # First, check for any files modified in the last 10 minutes
    sync_recent_changes(10)
    
    # Upload this script itself
    upload_self()
    
    print("===== GitHub Auto-Sync Complete =====\n")
    print("To run this automatically every hour, add a cron job:")
    print("0 * * * * python /path/to/auto_github_sync.py")
