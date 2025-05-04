import os
import logging
import discord
from discord.ext import commands
import discord.ext.commands as commands_ext

# Set up logging
logger = logging.getLogger(__name__)

# Initialize bot with all intents for full functionality
intents = discord.Intents.all()
bot = commands_ext.Bot(command_prefix="/", intents=intents)

# Bot events
@bot.event
async def on_ready():
    """Event triggered when bot is ready and connected to Discord"""
    logger.info(f"Bot is connected as {bot.user.name} ({bot.user.id})")
    
    # Log the number of servers the bot is in
    logger.info(f"Bot is in {len(bot.guilds)} servers")
    
    # Sync slash commands
    try:
        synced = await bot.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
    except Exception as e:
        logger.error(f"Failed to sync commands: {e}")
    
    # Set the bot status
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, 
        name="for /help"
    ))

@bot.event
async def on_guild_join(guild):
    """Event triggered when bot joins a new server"""
    logger.info(f"Bot joined a new guild: {guild.name} (id: {guild.id})")
    
    # Try to send a welcome message to the system channel if available
    if guild.system_channel:
        embed = discord.Embed(
            title="Thanks for adding me!",
            description="I'm a Roblox verification and moderation bot. Use `/help` to see available commands.",
            color=discord.Color.blue()
        )
        embed.add_field(name="Setup", value="First, make sure I have the necessary permissions for moderation commands.")
        embed.add_field(name="Verification", value="Use `/verify` to set up Roblox verification for your members.")
        
        try:
            await guild.system_channel.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for command errors"""
    if isinstance(error, commands.CommandNotFound):
        return
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing required argument: {error.param}")
    elif isinstance(error, commands.BadArgument):
        await ctx.send(f"Bad argument: {error}")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You don't have permission to use this command.")
    elif isinstance(error, commands.BotMissingPermissions):
        await ctx.send(f"I don't have the required permissions: {error.missing_perms}")
    else:
        logger.error(f"Unhandled command error: {error}")
        await ctx.send("An error occurred while executing the command.")

# Load cogs
async def load_extensions():
    """Load all cogs"""
    for filename in os.listdir('./cogs'):
        if filename.endswith('.py'):
            try:
                await bot.load_extension(f'cogs.{filename[:-3]}')
                logger.info(f"Loaded extension: {filename[:-3]}")
            except Exception as e:
                logger.error(f"Failed to load extension {filename}: {e}")

# Setup hook to load extensions when bot starts
@bot.event
async def setup_hook():
    """Setup hook that runs before the bot starts its connection to Discord"""
    await load_extensions()
