# Discord Bot with Roblox Integration

A Discord bot built with Python that provides Roblox verification, server management, and moderation features. The bot can verify Discord users with their Roblox accounts, manage server announcements, host events, and provide moderation tools.

## Features

- **Roblox Verification**: Link Discord users to their Roblox accounts with secure verification
- **Server Management**: Create announcements and host events with commands
- **Moderation Tools**: Commands for kick, ban, and timeout with proper permission checks
- **Roblox Ranking**: Rank users in Roblox groups (requires Roblox cookie)
- **Ticket System**: Create and manage support tickets with interactive buttons

## Commands

### Verification Commands
- `/verify <roblox_username>`: Start the verification process
- `/verify-confirm`: Confirm your verification after adding the code to your Roblox profile
- `/update <roblox_username>`: Update your linked Roblox account
- `/info-roblox <roblox_username>`: Get information about a Roblox user

### Moderation Commands
- `/kick <user> [reason]`: Kick a user from the server
- `/ban <user> [reason] [delete_days]`: Ban a user from the server
- `/timeout <user> <duration> [reason]`: Timeout a user in the server
- `/rank <roblox_username> <rank_name>`: Change a user's rank in Roblox group

### Server Management Commands
- `/announce <channel> <title> <message>`: Create an announcement
- `/host <channel> <event_type> <starts> <ends>`: Create a hosting announcement
- `/sendticket <channel>`: Set up a ticket system in a channel
- `/setup [verified_role] [announcement_channel] [host_channel]`: Set up server configuration

## Running the Bot

There are two components to this application:

1. **Web Application** - A Flask web server that provides a simple web interface and keeps the bot alive on hosting platforms
2. **Discord Bot** - The Discord bot that responds to commands and interacts with users

### Option 1: Run Everything Together (Recommended)

Use the supervisor script to run both the web server and Discord bot:

```bash
python supervisor.py
```

### Option 2: Run Components Separately

Run the web server:
```bash
gunicorn --bind 0.0.0.0:5000 main:app
```

Run the Discord bot:
```bash
python run_bot.py
```

## Environment Variables

Copy the `.env.example` file to `.env` and fill in the required environment variables:

- `DISCORD_TOKEN`: Your Discord bot token (required for bot functionality)
- `ROBLOX_COOKIE`: Roblox .ROBLOSECURITY cookie (required for ranking functionality)
- `SESSION_SECRET`: Secret key for Flask session encryption

## Database

The application uses PostgreSQL for data storage. Database connection settings are configured via environment variables:

- `DATABASE_URL`: PostgreSQL connection string

## Deploying on Render.com

This application is designed to be deployable on Render.com:

1. Create a new Web Service
2. Link your repository
3. Set the build command: `pip install -r requirements.txt`
4. Set the start command: `python supervisor.py`
5. Add the environment variables
6. Deploy the service

## License

MIT
