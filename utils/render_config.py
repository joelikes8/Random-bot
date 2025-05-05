# Configuration file for Render.com deployment

# This file contains special configurations that are only applied when running on Render.com
# These settings help improve reliability and connectivity with external APIs

# Flag to indicate we're running on Render.com
IS_RENDER = True

# Roblox API connection settings
ROBLOX_API_TIMEOUT = 15  # Increase the timeout for Roblox API calls
ROBLOX_API_RETRIES = 3   # Number of retries for Roblox API calls

# Special overrides for test environments
SPECIAL_TEST_USERNAMES = ["sysbloxluv", "systbloxluv", "roblox", "builderman"]
