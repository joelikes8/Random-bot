import discord
from discord import app_commands
from discord.ext import commands
import logging
import os
from datetime import datetime, timedelta

from utils.roblox_api import rank_user
from utils.embed_builder import create_embed

logger = logging.getLogger(__name__)

class Moderation(commands.Cog):
    """Handles moderation commands"""
    
    def __init__(self, bot):
        self.bot = bot
        self.roblox_cookie = os.getenv("ROBLOX_COOKIE")
    
    @app_commands.command(name="rank", description="Change a user's rank in Roblox")
    @app_commands.describe(
        roblox_username="The Roblox username of the user to rank",
        rank_name="The name of the rank to assign"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def rank(self, interaction: discord.Interaction, roblox_username: str, rank_name: str):
        """Rank a user in a Roblox group"""
        await interaction.response.defer(ephemeral=True)
        
        if not self.roblox_cookie:
            return await interaction.followup.send(
                "Roblox cookie is not configured. Please contact the bot administrator.",
                ephemeral=True
            )
        
        try:
            # Attempt to rank the user
            success, message = await rank_user(roblox_username, rank_name, self.roblox_cookie)
            
            if success:
                embed = create_embed(
                    title="Ranking Successful",
                    description=f"Successfully ranked {roblox_username} to {rank_name}.",
                    color=discord.Color.green()
                )
                
                # Log the rank change
                logger.info(f"{interaction.user.name} ({interaction.user.id}) ranked {roblox_username} to {rank_name}")
                
                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                embed = create_embed(
                    title="Ranking Failed",
                    description=f"Failed to rank {roblox_username}: {message}",
                    color=discord.Color.red()
                )
                
                await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in rank command: {e}")
            await interaction.followup.send(
                "An error occurred while ranking the user. Please try again later.",
                ephemeral=True
            )
    
    @rank.error
    async def rank_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Administrator permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in rank command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.describe(
        user="The user to kick",
        reason="The reason for kicking the user"
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str = "No reason provided"):
        """Kick a user from the server"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if the bot can kick the user
            if not interaction.guild.me.guild_permissions.kick_members:
                return await interaction.followup.send(
                    "I don't have permission to kick members.",
                    ephemeral=True
                )
            
            # Check if the user is higher in hierarchy than the bot
            if user.top_role >= interaction.guild.me.top_role:
                return await interaction.followup.send(
                    "I can't kick this user because they have a higher or equal role to me.",
                    ephemeral=True
                )
            
            # Check if the user is higher in hierarchy than the command user
            if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                return await interaction.followup.send(
                    "You can't kick this user because they have a higher or equal role to you.",
                    ephemeral=True
                )
            
            # Send a DM to the user (if possible)
            try:
                dm_embed = create_embed(
                    title=f"You've been kicked from {interaction.guild.name}",
                    description=f"Reason: {reason}",
                    color=discord.Color.red()
                )
                
                await user.send(embed=dm_embed)
            except Exception:
                logger.warning(f"Could not send DM to {user.name} ({user.id}) about being kicked")
            
            # Kick the user
            await interaction.guild.kick(user, reason=f"{interaction.user} - {reason}")
            
            # Log the kick
            logger.info(f"{interaction.user.name} ({interaction.user.id}) kicked {user.name} ({user.id}) for {reason}")
            
            # Send confirmation to the command user
            embed = create_embed(
                title="User Kicked",
                description=f"{user.mention} has been kicked from the server.",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="Reason", value=reason)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in kick command: {e}")
            await interaction.followup.send(
                "An error occurred while kicking the user. Please try again later.",
                ephemeral=True
            )
    
    @kick.error
    async def kick_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Kick Members permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in kick command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.describe(
        user="The user to ban",
        reason="The reason for banning the user",
        delete_days="Number of days of messages to delete (0-7)"
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.User, reason: str = "No reason provided", delete_days: int = 0):
        """Ban a user from the server"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Validate delete_days
            if delete_days < 0 or delete_days > 7:
                return await interaction.followup.send(
                    "Delete days must be between 0 and 7.",
                    ephemeral=True
                )
            
            # Check if the bot can ban members
            if not interaction.guild.me.guild_permissions.ban_members:
                return await interaction.followup.send(
                    "I don't have permission to ban members.",
                    ephemeral=True
                )
            
            # If the user is a member of the guild, we need to do additional checks
            member = interaction.guild.get_member(user.id)
            if member:
                # Check if the user is higher in hierarchy than the bot
                if member.top_role >= interaction.guild.me.top_role:
                    return await interaction.followup.send(
                        "I can't ban this user because they have a higher or equal role to me.",
                        ephemeral=True
                    )
                
                # Check if the user is higher in hierarchy than the command user
                if member.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                    return await interaction.followup.send(
                        "You can't ban this user because they have a higher or equal role to you.",
                        ephemeral=True
                    )
                
                # Send a DM to the user (if possible)
                try:
                    dm_embed = create_embed(
                        title=f"You've been banned from {interaction.guild.name}",
                        description=f"Reason: {reason}",
                        color=discord.Color.red()
                    )
                    
                    await user.send(embed=dm_embed)
                except Exception:
                    logger.warning(f"Could not send DM to {user.name} ({user.id}) about being banned")
            
            # Ban the user
            await interaction.guild.ban(user, reason=f"{interaction.user} - {reason}", delete_message_days=delete_days)
            
            # Log the ban
            logger.info(f"{interaction.user.name} ({interaction.user.id}) banned {user.name} ({user.id}) for {reason}")
            
            # Send confirmation to the command user
            embed = create_embed(
                title="User Banned",
                description=f"{user.mention} has been banned from the server.",
                color=discord.Color.red()
            )
            
            embed.add_field(name="Reason", value=reason)
            embed.add_field(name="Delete Messages", value=f"{delete_days} days")
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in ban command: {e}")
            await interaction.followup.send(
                "An error occurred while banning the user. Please try again later.",
                ephemeral=True
            )
    
    @ban.error
    async def ban_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Ban Members permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in ban command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="timeout", description="Timeout a user in the server")
    @app_commands.describe(
        user="The user to timeout",
        duration="Duration in minutes",
        reason="The reason for the timeout"
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(self, interaction: discord.Interaction, user: discord.Member, duration: int, reason: str = "No reason provided"):
        """Timeout a user in the server"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if the bot can timeout the user
            if not interaction.guild.me.guild_permissions.moderate_members:
                return await interaction.followup.send(
                    "I don't have permission to timeout members.",
                    ephemeral=True
                )
            
            # Check if the user is higher in hierarchy than the bot
            if user.top_role >= interaction.guild.me.top_role:
                return await interaction.followup.send(
                    "I can't timeout this user because they have a higher or equal role to me.",
                    ephemeral=True
                )
            
            # Check if the user is higher in hierarchy than the command user
            if user.top_role >= interaction.user.top_role and interaction.user.id != interaction.guild.owner_id:
                return await interaction.followup.send(
                    "You can't timeout this user because they have a higher or equal role to you.",
                    ephemeral=True
                )
            
            # Calculate the timeout duration
            timeout_duration = timedelta(minutes=duration)
            
            # Send a DM to the user (if possible)
            try:
                dm_embed = create_embed(
                    title=f"You've been timed out in {interaction.guild.name}",
                    description=f"Duration: {duration} minutes\nReason: {reason}",
                    color=discord.Color.orange()
                )
                
                await user.send(embed=dm_embed)
            except Exception:
                logger.warning(f"Could not send DM to {user.name} ({user.id}) about being timed out")
            
            # Timeout the user
            await user.timeout(timeout_duration, reason=f"{interaction.user} - {reason}")
            
            # Log the timeout
            logger.info(f"{interaction.user.name} ({interaction.user.id}) timed out {user.name} ({user.id}) for {duration} minutes: {reason}")
            
            # Send confirmation to the command user
            embed = create_embed(
                title="User Timed Out",
                description=f"{user.mention} has been timed out for {duration} minutes.",
                color=discord.Color.orange()
            )
            
            embed.add_field(name="Reason", value=reason)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in timeout command: {e}")
            await interaction.followup.send(
                "An error occurred while timing out the user. Please try again later.",
                ephemeral=True
            )
    
    @timeout.error
    async def timeout_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Moderate Members permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in timeout command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(Moderation(bot))
