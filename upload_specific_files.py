import github_upload

# List of files to upload
files_to_upload = [
    'utils/render_config.py',
    'utils/roblox_api.py',
    'cogs/verification.py'
]

# Upload each file
for file_path in files_to_upload:
    print(f"Uploading {file_path}...")
    github_upload.upload_file(file_path)
    print(f"Uploaded {file_path} successfully!")
