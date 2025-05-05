import os
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

# Check repository contents
response = requests.get(API_URL, headers=headers)

if response.status_code == 200:
    contents = response.json()
    print("Files in repository:")
    for item in contents:
        print(f"- {item['name']}")
    
    # Check cogs directory
    cogs_response = requests.get(f'{API_URL}/cogs', headers=headers)
    if cogs_response.status_code == 200:
        cogs_contents = cogs_response.json()
        print("\nFiles in cogs directory:")
        for item in cogs_contents:
            print(f"- {item['name']}")
    
    # Check utils directory
    utils_response = requests.get(f'{API_URL}/utils', headers=headers)
    if utils_response.status_code == 200:
        utils_contents = utils_response.json()
        print("\nFiles in utils directory:")
        for item in utils_contents:
            print(f"- {item['name']}")
    
    print("\nRepository URL: https://github.com/joelikes8/Random-bot")
else:
    print(f"Error: {response.status_code} {response.text}")
