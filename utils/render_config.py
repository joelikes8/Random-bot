# Configuration file for Render.com compatibility mode

# Enable Render.com compatibility mode for specific functionality
IS_RENDER = True

# Increase timeouts and retries to handle Render's network environment
ROBLOX_API_TIMEOUT = 20  # seconds
ROBLOX_API_RETRIES = 3

# Enable special test username handling
SPECIAL_TEST_USERNAMES = [
    "sysbloxluv", 
    "systbloxluv", 
    "roblox", 
    "builderman"
]

# Force username override is now disabled - verification will check for codes
FORCE_TEST_USERNAMES = False

# Map of test usernames to their Roblox IDs
TEST_USERNAME_IDS = {
    "sysbloxluv": "2470023",
    "systbloxluv": "2470023",
    "roblox": "1",
    "builderman": "156"
}
