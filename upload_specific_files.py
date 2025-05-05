import github_upload

# List of files to upload (recent changes)
files_to_upload = [
    'auto_github_sync.py',
    'upload_sync_script.py',
    'app.py',
    'models.py',
    '.env.example',
    'upload_specific_files.py'
]

# Upload each file
for file_path in files_to_upload:
    print(f"Uploading {file_path}...")
    github_upload.upload_file(file_path)
    print(f"Uploaded {file_path} successfully!")
