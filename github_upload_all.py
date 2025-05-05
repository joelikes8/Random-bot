import os
import logging
import sys

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# GITHUB_TOKEN environment variable check
def main():
    # Check if GITHUB_TOKEN is set
    if not os.environ.get('GITHUB_TOKEN'):
        logger.error("Missing GITHUB_TOKEN environment variable. Cannot upload to GitHub.")
        return
        
    logger.info("Starting GitHub upload process...")
    
    try:
        # Import and run all the GitHub upload scripts
        logger.info("Uploading cogs to GitHub...")
        import github_upload_cogs
        
        logger.info("Uploading env files to GitHub...")
        import github_upload_env
        
        logger.info("Uploading utils to GitHub...")
        import github_upload_utils
        
        logger.info("Updating Roblox cookie info in GitHub...")
        import github_update_cookie
        github_update_cookie.main()
        
        logger.info("GitHub upload process completed successfully!")
    except Exception as e:
        logger.error(f"Error during GitHub upload: {e}")

if __name__ == "__main__":
    main()
