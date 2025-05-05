#!/usr/bin/env python3
"""
GitHub Synchronization Script for Random-bot

This script synchronizes all project files with the GitHub repository.
It can be run manually or scheduled to run periodically.

Usage:
  python github_sync.py                   # Sync all files modified in the last hour
  python github_sync.py --all            # Sync all project files
  python github_sync.py --minutes 30     # Sync files modified in the last 30 minutes
  python github_sync.py --file main.py   # Sync only the specified file
"""

import os
import base64
import requests
import json
import time
import argparse
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

# File types to synchronize
PROJECT_FILE_TYPES = [
    '.py',                  # Python source files
    '.md',                  # Markdown documentation
    '.yaml', '.yml',        # YAML configuration files
    '.txt',                 # Text files
    '.json',                # JSON configuration files
    '.env.example',         # Example environment file
    '.replit',              # Replit configuration
    '.render_config.py'     # Render configuration
]

# Scripts that need special handling
SPECIAL_SCRIPTS = [
    'upload_',              # Upload scripts
    'github_',              # GitHub-related scripts
    'auto_'                 # Automation scripts
]

# Directories to include
INCLUDE_DIRS = [
    'cogs/',                # Bot command modules
    'utils/'                # Utility modules
]

# Directories to exclude
EXCLUDE_DIRS = [
    '.git/',                # Git directory
    '__pycache__/',         # Python cache
    '.cache/',              # Cache directory
    '.local/',              # Local configuration
    '.upm/'                 # Package manager directory
]

def upload_file(file_path, commit_message=None):
    """Upload a file to GitHub"""
    try:
        # Skip binary files and large files
        if file_path.endswith(('.png', '.jpg', '.jpeg', '.ico', '.gif', '.lock')) or \
           os.path.getsize(file_path) > 1000000:
            print(f"Skipping large or binary file: {file_path}")
            return False
           
        # Skip hidden files/directories except for important config files and scripts
        if ('/.' in file_path or file_path.startswith('.')) and \
           not any(important in file_path for important in ['.replit', '.env.example', '.render_config.py']) and \
           not any(script in file_path for script in SPECIAL_SCRIPTS):
            print(f"Skipping hidden file: {file_path}")
            return False
        
        # Skip non-project files
        if not any(file_path.endswith(ft) for ft in PROJECT_FILE_TYPES) and \
           not any(script in file_path for script in SPECIAL_SCRIPTS):
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

def get_modified_files(minutes=60):
    """Get files modified in the last X minutes"""
    modified_files = []
    
    # Use find command to get modified files
    try:
        # Construct a more targeted find command
        extensions_pattern = ' -o '.join(f'-name "*{ext}"' for ext in PROJECT_FILE_TYPES)
        special_scripts_pattern = ' -o '.join(f'-name "{script}*.py"' for script in SPECIAL_SCRIPTS)
        include_dirs_pattern = ' -o '.join(f'-path "./{dir}*"' for dir in INCLUDE_DIRS)
        exclude_dirs_pattern = ' '.join(f'-not -path "*/{dir}*"' for dir in EXCLUDE_DIRS)
        
        command = (
            f'find . -type f \( {extensions_pattern} -o {special_scripts_pattern} -o {include_dirs_pattern} \) '
            f'{exclude_dirs_pattern} -mmin -{minutes}'
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

def get_all_project_files():
    """Get all project files regardless of modification time"""
    all_files = []
    
    try:
        # Similar to get_modified_files but without the time constraint
        extensions_pattern = ' -o '.join(f'-name "*{ext}"' for ext in PROJECT_FILE_TYPES)
        special_scripts_pattern = ' -o '.join(f'-name "{script}*.py"' for script in SPECIAL_SCRIPTS)
        include_dirs_pattern = ' -o '.join(f'-path "./{dir}*"' for dir in INCLUDE_DIRS)
        exclude_dirs_pattern = ' '.join(f'-not -path "*/{dir}*"' for dir in EXCLUDE_DIRS)
        
        command = (
            f'find . -type f \( {extensions_pattern} -o {special_scripts_pattern} -o {include_dirs_pattern} \) '
            f'{exclude_dirs_pattern}'
        )
        
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        files = result.stdout.strip().split('\n')
        
        # Filter out empty lines and any remaining unwanted files
        for file in files:
            if file and os.path.isfile(file) and os.path.getsize(file) <= 1000000:
                all_files.append(file)
    except Exception as e:
        print(f"Error getting project files: {str(e)}")
    
    return all_files

def sync_files(files, delay=0.5):
    """Sync a list of files to GitHub"""
    print(f"Found {len(files)} files to sync")
    
    uploaded_count = 0
    failed_count = 0
    skipped_count = 0
    
    for file in files:
        try:
            success = upload_file(file)
            if success:
                uploaded_count += 1
            else:
                skipped_count += 1
            # Add a small delay to avoid rate limiting
            time.sleep(delay)
        except Exception as e:
            print(f"Error processing {file}: {str(e)}")
            failed_count += 1
    
    print(f"\nSummary:")
    print(f"  - Uploaded: {uploaded_count} files")
    print(f"  - Skipped:  {skipped_count} files")
    print(f"  - Failed:   {failed_count} files")
    
    return uploaded_count

def upload_self():
    """Upload this script itself"""
    return upload_file('github_sync.py', 'Update GitHub sync script')

def setup_argument_parser():
    """Set up command-line argument parsing"""
    parser = argparse.ArgumentParser(description='Synchronize project files with GitHub repository')
    parser.add_argument('--all', action='store_true', help='Sync all project files')
    parser.add_argument('--minutes', type=int, default=60, help='Sync files modified in the last N minutes')
    parser.add_argument('--file', type=str, help='Sync only the specified file')
    return parser

# Main execution
if __name__ == "__main__":
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    print("===== Starting GitHub Synchronization =====")
    print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if args.file:
        # Sync a specific file
        print(f"Syncing specific file: {args.file}")
        upload_file(args.file)
    elif args.all:
        # Sync all project files
        print("Syncing all project files...")
        files = get_all_project_files()
        sync_files(files)
    else:
        # Sync recently modified files
        print(f"Syncing files modified in the last {args.minutes} minutes...")
        files = get_modified_files(args.minutes)
        sync_files(files)
    
    # Always upload this script itself
    upload_self()
    
    print("\n===== GitHub Synchronization Complete =====")
    print("Usage tips:")
    print("  - Run 'python github_sync.py --all' to sync all project files")
    print("  - Run 'python github_sync.py --minutes 30' to sync files modified in the last 30 minutes")
    print("  - Run 'python github_sync.py --file app.py' to sync only the specified file")
    print("  - To run automatically every hour, add a cron job:")
    print("    0 * * * * python /path/to/github_sync.py")
