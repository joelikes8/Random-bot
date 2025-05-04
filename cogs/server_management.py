import discord
from discord import app_commands
from discord.ext import commands
import logging
from datetime import datetime
import asyncio

from app import db
from models import ServerConfig, HostedEvent
from utils.embed_builder import create_embed
from utils.ticket_system import create_ticket_button

logger = logging.getLogger(__name__)

class ServerManagement(commands.Cog):
    """Handles server management commands"""
    
    def __init__(self, bot):
        self.bot = bot
    
    @app_commands.command(name="host", description="Create a hosting announcement")
    @app_commands.describe(
        channel="The channel to send the hosting announcement to",
        event_type="What kind of event (tryout/training/etc.)",
        starts="When the event starts (YYYY-MM-DD HH:MM or '1 minute', '5 minutes', '10 minutes', etc.)",
        ends="When the event ends (YYYY-MM-DD HH:MM or '5 minutes', '10 minutes', etc.)"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def host(
        self, 
        interaction: discord.Interaction, 
        channel: discord.TextChannel,
        event_type: str,
        starts: str,
        ends: str
    ):
        """Create a hosting announcement"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            now = datetime.utcnow()
            
            # Parse the start time - check for relative time formats first
            try:
                # Check for relative time formats for start time
                if starts.lower().endswith('minute') or starts.lower().endswith('minutes'):
                    # Extract the number part
                    minutes_str = ''.join(filter(str.isdigit, starts))
                    if minutes_str and int(minutes_str) >= 0 and int(minutes_str) <= 30:
                        minutes = int(minutes_str)
                        # Calculate start_time as now + minutes
                        from datetime import timedelta
                        start_time = now + timedelta(minutes=minutes)
                        logger.info(f"Parsed relative start time: {minutes} minutes from now")
                    else:
                        return await interaction.followup.send(
                            "For start time in minutes, please use a value between 0 and 30 minutes.",
                            ephemeral=True
                        )
                else:
                    # Try standard datetime format
                    start_time = datetime.strptime(starts, "%Y-%m-%d %H:%M")
            except (ValueError, AttributeError) as e:
                logger.error(f"Error parsing start time: {e}")
                return await interaction.followup.send(
                    "Invalid start time format. Please use YYYY-MM-DD HH:MM or a relative time like '5 minutes'.",
                    ephemeral=True
                )
                
            # Parse the end time - check for relative time formats first
            try:
                # Check for relative time formats for end time
                if ends.lower().endswith('minute') or ends.lower().endswith('minutes'):
                    # Extract the number part
                    minutes_str = ''.join(filter(str.isdigit, ends))
                    if minutes_str and int(minutes_str) in [5, 10]:
                        minutes = int(minutes_str)
                        # Calculate end_time as start_time + minutes
                        from datetime import timedelta
                        end_time = start_time + timedelta(minutes=minutes)
                        logger.info(f"Parsed relative end time: {minutes} minutes from start time")
                    else:
                        return await interaction.followup.send(
                            "For end time in minutes, please use either 5 or 10 minutes.",
                            ephemeral=True
                        )
                else:
                    # Try standard datetime format
                    end_time = datetime.strptime(ends, "%Y-%m-%d %H:%M")
            except (ValueError, AttributeError) as e:
                logger.error(f"Error parsing end time: {e}")
                return await interaction.followup.send(
                    "Invalid end time format. Please use YYYY-MM-DD HH:MM or a relative time like '5 minutes' or '10 minutes'.",
                    ephemeral=True
                )
            
            # Check if end time is after start time
            if end_time <= start_time:
                return await interaction.followup.send(
                    "End time must be after start time.",
                    ephemeral=True
                )
            
            # Check if the bot has permission to send messages in the specified channel
            if not channel.permissions_for(interaction.guild.me).send_messages:
                return await interaction.followup.send(
                    f"I don't have permission to send messages in {channel.mention}.",
                    ephemeral=True
                )
            
            # Create the hosting announcement embed
            embed = create_embed(
                title=f"📢 {event_type.title()} Event",
                description=f"A new {event_type.lower()} event has been scheduled.",
                color=discord.Color.blue()
            )
            
            # Determine if we're using relative or absolute times for display
            now = datetime.utcnow()
            start_time_diff_minutes = int((start_time - now).total_seconds() / 60)
            end_time_diff_minutes = int((end_time - start_time).total_seconds() / 60)
            
            # Format start time display
            if start_time_diff_minutes <= 30:  # If it's a short time from now
                start_display = f"In {start_time_diff_minutes} minute{'s' if start_time_diff_minutes != 1 else ''} ({start_time.strftime('%H:%M UTC')})"
            else:
                start_display = start_time.strftime("%Y-%m-%d %H:%M UTC")
            
            # Format end time display
            if end_time_diff_minutes <= 30:  # If it's a short event
                end_display = f"Lasts {end_time_diff_minutes} minute{'s' if end_time_diff_minutes != 1 else ''} (until {end_time.strftime('%H:%M UTC')})"
            else:
                end_display = end_time.strftime("%Y-%m-%d %H:%M UTC")
            
            embed.add_field(name="Host", value=interaction.user.mention, inline=True)
            embed.add_field(name="Event Type", value=event_type.title(), inline=True)
            embed.add_field(name="Start Time", value=start_display, inline=True)
            embed.add_field(name="End Time", value=end_display, inline=True)
            
            embed.set_footer(text=f"Posted by {interaction.user.name} • {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
            
            # Send the announcement to the specified channel
            try:
                announcement = await channel.send(embed=embed)
                
                # Save the hosted event to the database
                # Import app context function
                from app import with_app_context
                
                @with_app_context
                def save_event_to_db():
                    try:
                        from models import HostedEvent
                        new_event = HostedEvent(
                            guild_id=str(interaction.guild.id),
                            host_id=str(interaction.user.id),
                            event_type=event_type,
                            start_time=start_time,
                            end_time=end_time,
                            message_id=str(announcement.id),
                            channel_id=str(channel.id)
                        )
                        
                        db.session.add(new_event)
                        db.session.commit()
                        logger.info(f"Successfully saved hosted event to database")
                        return True
                    except Exception as e:
                        logger.error(f"Error saving event to database: {e}")
                        return False
                
                # Call the function to save the event
                save_event_to_db()
                
                # Send confirmation to the command user
                confirm_embed = create_embed(
                    title="Hosting Announcement Created",
                    description=f"Your {event_type} announcement has been posted in {channel.mention}.",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=confirm_embed, ephemeral=True)
            
            except Exception as e:
                logger.error(f"Error sending hosting announcement: {e}")
                await interaction.followup.send(
                    f"An error occurred while sending the announcement to {channel.mention}.",
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error in host command: {e}")
            await interaction.followup.send(
                "An error occurred while creating the hosting announcement. Please try again later.",
                ephemeral=True
            )
    
    @host.error
    async def host_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Manage Messages permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in host command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="announce", description="Create an announcement")
    @app_commands.describe(
        channel="The channel to send the announcement to",
        title="The title of the announcement",
        message="The message of the announcement"
    )
    @app_commands.checks.has_permissions(manage_messages=True)
    async def announce(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        title: str,
        message: str
    ):
        """Create an announcement"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if the bot has permission to send messages in the specified channel
            if not channel.permissions_for(interaction.guild.me).send_messages:
                return await interaction.followup.send(
                    f"I don't have permission to send messages in {channel.mention}.",
                    ephemeral=True
                )
            
            # Create the announcement embed
            embed = create_embed(
                title=title,
                description=message,
                color=discord.Color.blue()
            )
            
            embed.set_footer(text=f"Posted by {interaction.user.name} • {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
            
            # Send the announcement to the specified channel
            try:
                await channel.send(embed=embed)
                
                # Send confirmation to the command user
                confirm_embed = create_embed(
                    title="Announcement Created",
                    description=f"Your announcement has been posted in {channel.mention}.",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=confirm_embed, ephemeral=True)
            
            except Exception as e:
                logger.error(f"Error sending announcement: {e}")
                await interaction.followup.send(
                    f"An error occurred while sending the announcement to {channel.mention}.",
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error in announce command: {e}")
            await interaction.followup.send(
                "An error occurred while creating the announcement. Please try again later.",
                ephemeral=True
            )
    
    @announce.error
    async def announce_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Manage Messages permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in announce command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="sendticket", description="Set up a ticket system in a channel")
    @app_commands.describe(
        channel="The channel to set up the ticket system in"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def sendticket(self, interaction: discord.Interaction, channel: discord.TextChannel):
        """Set up a ticket system in a channel"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Check if the bot has permission to send messages in the specified channel
            if not channel.permissions_for(interaction.guild.me).send_messages:
                return await interaction.followup.send(
                    f"I don't have permission to send messages in {channel.mention}.",
                    ephemeral=True
                )
            
            # Create the ticket system embed
            embed = create_embed(
                title="🎫 Support Tickets",
                description="Click the button below to open a support ticket. A staff member will assist you as soon as possible.",
                color=discord.Color.green()
            )
            
            # Create the ticket button
            view = create_ticket_button(self.bot)
            
            # Send the ticket system message to the specified channel
            try:
                await channel.send(embed=embed, view=view)
                
                # Update the server config with the ticket channel
                # Import app context function
                from app import with_app_context
                
                @with_app_context
                def update_server_config():
                    try:
                        from models import ServerConfig
                        server_config = ServerConfig.query.filter_by(guild_id=str(interaction.guild.id)).first()
                        
                        if server_config:
                            server_config.ticket_channel_id = str(channel.id)
                        else:
                            server_config = ServerConfig(
                                guild_id=str(interaction.guild.id),
                                ticket_channel_id=str(channel.id)
                            )
                            db.session.add(server_config)
                        
                        db.session.commit()
                        logger.info(f"Updated server config with ticket channel ID: {channel.id}")
                        return True
                    except Exception as e:
                        logger.error(f"Error updating server config: {e}")
                        return False
                
                # Call the function to update the server config
                update_server_config()
                
                # Send confirmation to the command user
                confirm_embed = create_embed(
                    title="Ticket System Set Up",
                    description=f"Ticket system has been set up in {channel.mention}.",
                    color=discord.Color.green()
                )
                
                await interaction.followup.send(embed=confirm_embed, ephemeral=True)
            
            except Exception as e:
                logger.error(f"Error setting up ticket system: {e}")
                await interaction.followup.send(
                    f"An error occurred while setting up the ticket system in {channel.mention}.",
                    ephemeral=True
                )
        
        except Exception as e:
            logger.error(f"Error in sendticket command: {e}")
            await interaction.followup.send(
                "An error occurred while setting up the ticket system. Please try again later.",
                ephemeral=True
            )
    
    @sendticket.error
    async def sendticket_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Administrator permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in sendticket command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )
    
    @app_commands.command(name="setup", description="Set up server configuration")
    @app_commands.describe(
        verified_role="The role to give to verified users",
        announcement_channel="The default channel for announcements",
        host_channel="The default channel for hosting announcements"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup(
        self,
        interaction: discord.Interaction,
        verified_role: discord.Role = None,
        announcement_channel: discord.TextChannel = None,
        host_channel: discord.TextChannel = None
    ):
        """Set up server configuration"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Import app context function
            from app import with_app_context
            
            @with_app_context
            def update_server_config():
                try:
                    from models import ServerConfig
                    server_config = ServerConfig.query.filter_by(guild_id=str(interaction.guild.id)).first()
                    
                    if not server_config:
                        server_config = ServerConfig(guild_id=str(interaction.guild.id))
                        db.session.add(server_config)
                    
                    # Update the server config with the provided values
                    if verified_role:
                        server_config.verified_role_id = str(verified_role.id)
                    
                    if announcement_channel:
                        server_config.announcement_channel_id = str(announcement_channel.id)
                    
                    if host_channel:
                        server_config.host_channel_id = str(host_channel.id)
                    
                    db.session.commit()
                    logger.info(f"Updated server config for guild {interaction.guild.id}")
                    return True
                except Exception as e:
                    logger.error(f"Error updating server config: {e}")
                    return False
            
            # Call the function to update the server config
            success = update_server_config()
            if not success:
                return await interaction.followup.send(
                    "An error occurred while updating the server configuration. Please try again later.",
                    ephemeral=True
                )
            
            # Create a response embed
            embed = create_embed(
                title="Server Configuration Updated",
                description="The server configuration has been updated.",
                color=discord.Color.green()
            )
            
            if verified_role:
                embed.add_field(name="Verified Role", value=verified_role.mention)
            
            if announcement_channel:
                embed.add_field(name="Announcement Channel", value=announcement_channel.mention)
            
            if host_channel:
                embed.add_field(name="Host Channel", value=host_channel.mention)
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in setup command: {e}")
            await interaction.followup.send(
                "An error occurred while setting up the server configuration. Please try again later.",
                ephemeral=True
            )
    
    @setup.error
    async def setup_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Administrator permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in setup command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )

    @app_commands.command(name="setup_ticket_roles", description="Set up roles that can access tickets")
    @app_commands.describe(
        verified_role="The main verified role (optional)",
        role_ids="Comma-separated list of role IDs that can access tickets"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def setup_ticket_roles(
        self,
        interaction: discord.Interaction,
        verified_role: discord.Role = None,
        role_ids: str = ""
    ):
        """Set up roles that can access tickets"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Import app context function
            from app import with_app_context
            
            # Parse role IDs
            roles_to_add = []
            if role_ids:
                # Remove any whitespace and split by commas
                role_id_list = [r.strip() for r in role_ids.replace(' ', '').split(',')]
                # Filter out empty strings
                role_id_list = [r for r in role_id_list if r]
                for role_id in role_id_list:
                    try:
                        # Validate role ID
                        role_id = str(int(role_id))  # Will raise ValueError if not a number
                        roles_to_add.append(role_id)
                    except ValueError:
                        logger.warning(f"Invalid role ID: {role_id}")
            
            @with_app_context
            def update_ticket_roles():
                try:
                    from models import TicketRole
                    
                    # First, delete existing ticket roles for this guild
                    existing_roles = TicketRole.query.filter_by(guild_id=str(interaction.guild.id)).all()
                    for role in existing_roles:
                        db.session.delete(role)
                    
                    # Add verified role if provided
                    if verified_role:
                        verified_role_entry = TicketRole(
                            guild_id=str(interaction.guild.id),
                            role_id=str(verified_role.id),
                            is_verified_role=True
                        )
                        db.session.add(verified_role_entry)
                    
                    # Add other ticket access roles
                    for role_id in roles_to_add:
                        role_entry = TicketRole(
                            guild_id=str(interaction.guild.id),
                            role_id=role_id,
                            is_verified_role=False
                        )
                        db.session.add(role_entry)
                    
                    db.session.commit()
                    logger.info(f"Updated ticket roles for guild {interaction.guild.id}")
                    return True, len(roles_to_add) + (1 if verified_role else 0)
                except Exception as e:
                    logger.error(f"Error updating ticket roles: {e}")
                    return False, 0
            
            # Update ticket roles
            success, roles_count = update_ticket_roles()
            if not success:
                return await interaction.followup.send(
                    "An error occurred while updating ticket roles. Please try again later.",
                    ephemeral=True
                )
            
            # Create response embed
            embed = create_embed(
                title="Ticket Roles Updated",
                description=f"Successfully configured {roles_count} role{'s' if roles_count != 1 else ''} for ticket access.",
                color=discord.Color.green()
            )
            
            # Add verified role if provided
            if verified_role:
                embed.add_field(name="Verified Role", value=verified_role.mention, inline=False)
            
            # Add other roles if provided
            if roles_to_add:
                role_mentions = []
                for role_id in roles_to_add:
                    role = interaction.guild.get_role(int(role_id))
                    if role:
                        role_mentions.append(role.mention)
                    else:
                        role_mentions.append(f"<@&{role_id}> (Not found)")
                
                embed.add_field(
                    name="Ticket Access Roles", 
                    value="\n".join(role_mentions) if role_mentions else "None", 
                    inline=False
                )
            
            await interaction.followup.send(embed=embed, ephemeral=True)
        
        except Exception as e:
            logger.error(f"Error in setup_ticket_roles command: {e}")
            await interaction.followup.send(
                "An error occurred while setting up ticket roles. Please try again later.",
                ephemeral=True
            )
    
    @setup_ticket_roles.error
    async def setup_ticket_roles_error(self, interaction: discord.Interaction, error):
        if isinstance(error, app_commands.errors.MissingPermissions):
            await interaction.response.send_message(
                "You don't have permission to use this command. You need the Administrator permission.",
                ephemeral=True
            )
        else:
            logger.error(f"Unhandled error in setup_ticket_roles command: {error}")
            await interaction.response.send_message(
                "An error occurred while executing the command.",
                ephemeral=True
            )

async def setup(bot):
    from models import ServerConfig, TicketRole
    await bot.add_cog(ServerManagement(bot))
