import os
import aiohttp
import asyncio
import json
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def login_to_roblox():
    """Login to Roblox and get a valid .ROBLOSECURITY cookie"""
    username = os.environ.get('ROBLOX_USERNAME')
    password = os.environ.get('ROBLOX_PASSWORD')
    
    if not username or not password:
        logger.error("ROBLOX_USERNAME or ROBLOX_PASSWORD environment variables not set")
        return False, "Missing Roblox credentials"
    
    try:
        # Step 1: Get the CSRF token
        async with aiohttp.ClientSession() as session:
            # First, visit the login page to get initial cookies
            login_url = "https://www.roblox.com/login"
            logger.info(f"Requesting login page: {login_url}")
            async with session.get(login_url) as response:
                if response.status != 200:
                    logger.error(f"Failed to access login page: {response.status}")
                    return False, f"Failed to access login page: {response.status}"
                
                cookies = session.cookie_jar.filter_cookies('https://www.roblox.com')
                logger.info(f"Got {len(cookies)} cookies from initial page load")
                
                # Get the login page content to extract the request verification token
                page_content = await response.text()
                
                # Extract verification token
                token_match = re.search(r'data-token="([^"]+)"', page_content)
                if not token_match:
                    logger.error("Could not find verification token in login page")
                    return False, "Could not find verification token"
                
                verification_token = token_match.group(1)
                logger.info(f"Found verification token: {verification_token[:10]}...")
                
                # Step 2: Attempt to login
                login_api_url = "https://auth.roblox.com/v2/login"
                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    "X-CSRF-TOKEN": verification_token,
                    "Origin": "https://www.roblox.com",
                    "Referer": "https://www.roblox.com/login"
                }
                
                payload = {
                    "cvalue": username,
                    "ctype": "Username",
                    "password": password,
                    "captchaToken": "",
                    "captchaProvider": "reCAPTCHA"
                }
                
                logger.info(f"Attempting to login as {username}")
                async with session.post(login_api_url, json=payload, headers=headers) as login_response:
                    response_text = await login_response.text()
                    logger.info(f"Login response status: {login_response.status}")
                    
                    # Check for successful login (200 status and .ROBLOSECURITY cookie)
                    if login_response.status == 200:
                        # Get the .ROBLOSECURITY cookie
                        cookies = session.cookie_jar.filter_cookies('https://www.roblox.com')
                        roblosecurity = None
                        
                        for cookie in cookies:
                            if cookie.key == '.ROBLOSECURITY':
                                roblosecurity = cookie.value
                                break
                        
                        if roblosecurity:
                            logger.info(f"Successfully obtained .ROBLOSECURITY cookie of length {len(roblosecurity)}")
                            return True, roblosecurity
                        else:
                            logger.error("Login appeared successful, but no .ROBLOSECURITY cookie found")
                            return False, "No .ROBLOSECURITY cookie found after login"
                    else:
                        # Try to parse error message
                        try:
                            error_data = json.loads(response_text)
                            error_message = "Unknown error"
                            if "errors" in error_data and error_data["errors"]:
                                error_message = error_data["errors"][0].get("message", "Unknown error")
                            logger.error(f"Login failed: {error_message}")
                            return False, f"Login failed: {error_message}"
                        except Exception as e:
                            logger.error(f"Failed to parse login error: {e}")
                            logger.error(f"Raw response: {response_text[:200]}...")
                            return False, f"Login failed with status {login_response.status}"
    
    except Exception as e:
        logger.error(f"Error during login: {e}")
        return False, f"Login error: {str(e)}"

async def join_group_with_credentials(group_id):
    """Login to Roblox and join the specified group"""
    success, result = await login_to_roblox()
    
    if not success:
        return False, f"Failed to login to Roblox: {result}"
    
    # We now have a valid .ROBLOSECURITY cookie
    roblosecurity = result
    logger.info(f"Successfully logged in, now joining group {group_id}")
    
    try:
        # First, get a CSRF token
        token_url = "https://auth.roblox.com/v2/logout"
        
        headers = {
            "Cookie": f".ROBLOSECURITY={roblosecurity}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        async with aiohttp.ClientSession() as session:
            # Check if we're authenticated
            auth_check_url = "https://users.roblox.com/v1/users/authenticated"
            async with session.get(auth_check_url, headers=headers) as auth_response:
                auth_status = await auth_response.text()
                logger.info(f"Authentication check response: {auth_status[:100]}")
                
                if auth_response.status != 200:
                    logger.error(f"Failed to authenticate with Roblox: Status {auth_response.status}")
                    return False, f"Failed to authenticate with Roblox: Status {auth_response.status}"
            
            # Get CSRF token
            async with session.post(token_url, headers=headers) as response:
                if response.status == 403:
                    csrf_token = response.headers.get("x-csrf-token")
                    if csrf_token:
                        logger.info(f"Got CSRF token: {csrf_token[:5]}...")
                        headers["x-csrf-token"] = csrf_token
                    else:
                        logger.error("Failed to get CSRF token")
                        return False, "Failed to get CSRF token"
                else:
                    logger.error(f"Unexpected response when getting CSRF token: {response.status}")
                    return False, f"Unexpected response: {response.status}"
            
            # Join the group
            url = f"https://groups.roblox.com/v1/groups/{group_id}/users"
            
            async with session.post(url, headers=headers, json={}) as response:
                response_text = await response.text()
                logger.info(f"Join group response status: {response.status}")
                logger.info(f"Join group response: {response_text[:100]}")
                
                if response.status == 200:
                    logger.info(f"Successfully joined group {group_id}")
                    return True, "Successfully joined group"
                else:
                    try:
                        if response_text:
                            error_data = json.loads(response_text)
                            if "errors" in error_data and error_data["errors"]:
                                error_message = error_data["errors"][0].get("message", "Unknown error")
                                logger.error(f"Failed to join group: {error_message}")
                                return False, f"Failed to join group: {error_message}"
                    except Exception as e:
                        logger.error(f"Failed to parse error response: {e}")
                    
                    return False, f"Failed to join group, status code: {response.status}"
                    
    except Exception as e:
        logger.error(f"Error joining group: {e}")
        return False, f"Error joining group: {str(e)}"

async def update_cookie_in_env():
    """Login to Roblox and update the ROBLOX_COOKIE environment variable"""
    success, result = await login_to_roblox()
    
    if not success:
        return False, f"Failed to login to Roblox: {result}"
    
    # We now have a valid .ROBLOSECURITY cookie
    roblosecurity = result
    
    # Update the environment variable
    os.environ['ROBLOX_COOKIE'] = roblosecurity
    logger.info("Updated ROBLOX_COOKIE environment variable with fresh cookie")
    
    return True, "Successfully updated ROBLOX_COOKIE environment variable"

async def main():
    # The USMC Group ID
    GROUP_ID = '11966964'
    
    # First try to get a fresh cookie
    logger.info("Attempting to get a fresh Roblox cookie...")
    cookie_success, cookie_message = await update_cookie_in_env()
    if cookie_success:
        logger.info("Successfully updated Roblox cookie")
    else:
        logger.error(f"Failed to update Roblox cookie: {cookie_message}")
    
    # Now try to join the group
    logger.info(f"Attempting to join Roblox group {GROUP_ID}...")
    success, message = await join_group_with_credentials(GROUP_ID)
    
    if success:
        logger.info(f"SUCCESS: Bot successfully joined the USMC Roblox group: {message}")
        print(f"SUCCESS: Bot successfully joined the USMC Roblox group")
    else:
        logger.error(f"ERROR: Bot failed to join the USMC Roblox group. Reason: {message}")
        print(f"ERROR: Bot failed to join the USMC Roblox group. Reason: {message}")

if __name__ == "__main__":
    asyncio.run(main())
