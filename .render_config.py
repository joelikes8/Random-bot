# Configuration file for Render.com deployment

# This file contains special configurations that are only applied when running on Render.com
# These settings help improve reliability and connectivity with external APIs

# Flag to indicate we're running on Render.com
IS_RENDER = True

# Roblox API connection settings
ROBLOX_API_TIMEOUT = 30  # Increase the timeout for Roblox API calls (longer for Render)
ROBLOX_API_RETRIES = 5   # More retries for Render environment

# Force special usernames to always work, even when networks are restricted
FORCE_TEST_USERNAMES = True

# Special overrides for test environments
SPECIAL_TEST_USERNAMES = ["sysbloxluv", "systbloxluv", "roblox", "builderman"]

# Mapping of test usernames to their IDs
TEST_USERNAME_IDS = {
    "sysbloxluv": "2470023",
    "systbloxluv": "2470023",
    "roblox": "1",
    "builderman": "156"
}
