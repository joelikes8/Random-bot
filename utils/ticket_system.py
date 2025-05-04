import discord
import logging
from datetime import datetime
import asyncio

from app import db, with_app_context
from models import Ticket
from utils.embed_builder import create_embed

logger = logging.getLogger(__name__)

class TicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Create Ticket", custom_id="create_ticket", style=discord.ButtonStyle.green, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to create a support ticket"""
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Import app context function
            from app import with_app_context
            
            # Check if the user already has an open ticket
            @with_app_context
            def check_existing_ticket():
                try:
                    from models import Ticket
                    existing_ticket = Ticket.query.filter_by(
                        guild_id=str(interaction.guild.id),
                        user_id=str(interaction.user.id),
                        status="open"
                    ).first()
                    return existing_ticket
                except Exception as e:
                    logger.error(f"Error checking existing ticket: {e}")
                    return None
            
            # Update ticket status if channel was deleted
            @with_app_context
            def close_existing_ticket(ticket_id):
                try:
                    from models import Ticket
                    existing_ticket = Ticket.query.get(ticket_id)
                    if existing_ticket:
                        existing_ticket.status = "closed"
                        existing_ticket.closed_at = datetime.utcnow()
                        db.session.commit()
                        logger.info(f"Closed ticket {ticket_id} because channel was deleted")
                    return True
                except Exception as e:
                    logger.error(f"Error closing existing ticket: {e}")
                    return False
            
            # Check for existing open ticket
            existing_ticket = check_existing_ticket()
            if existing_ticket:
                # Try to get the channel
                channel = interaction.guild.get_channel(int(existing_ticket.channel_id))
                
                if channel:
                    return await interaction.followup.send(
                        f"You already have an open ticket: {channel.mention}",
                        ephemeral=True
                    )
                else:
                    # Channel was deleted, update the ticket status
                    close_existing_ticket(existing_ticket.id)
            
            # Create a new ticket channel
            overwrites = {
                interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                interaction.guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True),
                interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
            }
            
            # Add configured ticket roles and admin roles to the channel overwrites
            @with_app_context
            def get_ticket_roles():
                try:
                    from models import TicketRole
                    ticket_roles = TicketRole.query.filter_by(guild_id=str(interaction.guild.id)).all()
                    return ticket_roles
                except Exception as e:
                    logger.error(f"Error getting ticket roles: {e}")
                    return []
            
            # Get configured ticket roles
            ticket_roles = get_ticket_roles()
            ticket_role_ids = [role.role_id for role in ticket_roles]
            
            try:
                # First add explicitly configured roles
                for role_id in ticket_role_ids:
                    try:
                        role = interaction.guild.get_role(int(role_id))
                        if role:
                            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
                    except ValueError:
                        continue
                
                # Then add admin/mod roles as fallback
                for role in interaction.guild.roles:
                    # Check for admin or moderator roles by name or permissions
                    if (
                        role.permissions.administrator or
                        role.permissions.manage_guild or
                        any(name in role.name.lower() for name in ["admin", "mod", "staff", "support"])
                    ):
                        overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
            except Exception as e:
                logger.error(f"Error adding roles to ticket channel overwrites: {e}")
            
            # Create the channel in a ticket category if it exists, otherwise in the guild
            category = None
            try:
                # Look for a category with "ticket" in the name
                for cat in interaction.guild.categories:
                    if "ticket" in cat.name.lower():
                        category = cat
                        break
            except Exception as e:
                logger.error(f"Error finding ticket category: {e}")
            
            # Get the latest ticket number
            @with_app_context
            def get_latest_ticket_number():
                try:
                    from models import Ticket
                    latest_ticket = Ticket.query.filter_by(
                        guild_id=str(interaction.guild.id)
                    ).order_by(Ticket.id.desc()).first()
                    
                    if latest_ticket:
                        return latest_ticket.id + 1
                    return 1
                except Exception as e:
                    logger.error(f"Error getting latest ticket number: {e}")
                    return 1
            
            # Get the ticket number
            ticket_number = get_latest_ticket_number()
            
            # Create the ticket channel
            channel_name = f"ticket-{interaction.user.name}-{ticket_number}"
            try:
                ticket_channel = await interaction.guild.create_text_channel(
                    name=channel_name,
                    overwrites=overwrites,
                    category=category,
                    topic=f"Support ticket for {interaction.user.name} ({interaction.user.id})"
                )
            except discord.Forbidden:
                return await interaction.followup.send(
                    "I don't have permission to create channels. Please contact an administrator.",
                    ephemeral=True
                )
            except Exception as e:
                logger.error(f"Error creating ticket channel: {e}")
                return await interaction.followup.send(
                    "An error occurred while creating your ticket. Please try again later.",
                    ephemeral=True
                )
            
            # Create and save the ticket in the database
            @with_app_context
            def create_ticket_in_db():
                try:
                    from models import Ticket
                    new_ticket = Ticket(
                        guild_id=str(interaction.guild.id),
                        channel_id=str(ticket_channel.id),
                        user_id=str(interaction.user.id),
                        status="open",
                        created_at=datetime.utcnow()
                    )
                    
                    db.session.add(new_ticket)
                    db.session.commit()
                    logger.info(f"Created new ticket in database for channel: {ticket_channel.id}")
                    return True
                except Exception as e:
                    logger.error(f"Error creating ticket in database: {e}")
                    return False
            
            # Save the ticket
            create_ticket_in_db()
            
            # Create close ticket button
            close_view = CloseTicketView(self.bot)
            
            # Send initial message in the ticket channel
            embed = create_embed(
                title="Support Ticket",
                description=f"Ticket created by {interaction.user.mention}",
                color=discord.Color.green()
            )
            
            embed.add_field(
                name="Instructions",
                value="Please describe your issue and a staff member will assist you soon.",
                inline=False
            )
            
            await ticket_channel.send(embed=embed, view=close_view)
            
            # Ping the user in the channel
            await ticket_channel.send(f"{interaction.user.mention}")
            
            # Send confirmation to the user
            await interaction.followup.send(
                f"Your ticket has been created: {ticket_channel.mention}",
                ephemeral=True
            )
        
        except Exception as e:
            logger.error(f"Error in create_ticket button: {e}")
            await interaction.followup.send(
                "An error occurred while creating your ticket. Please try again later.",
                ephemeral=True
            )

class CloseTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Close Ticket", custom_id="close_ticket", style=discord.ButtonStyle.red, emoji="🔒")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to close a support ticket"""
        await interaction.response.defer()
        
        try:
            # Import app context function
            from app import with_app_context
            
            # Find and update the ticket
            @with_app_context
            def close_ticket_in_db():
                try:
                    from models import Ticket
                    ticket = Ticket.query.filter_by(
                        channel_id=str(interaction.channel.id),
                        status="open"
                    ).first()
                    
                    if not ticket:
                        return None
                    
                    # Update the ticket status
                    ticket.status = "closed"
                    ticket.closed_at = datetime.utcnow()
                    db.session.commit()
                    logger.info(f"Closed ticket in database for channel: {interaction.channel.id}")
                    return ticket
                except Exception as e:
                    logger.error(f"Error closing ticket in database: {e}")
                    return None
            
            # Close the ticket
            ticket = close_ticket_in_db()
            if not ticket:
                return await interaction.followup.send(
                    "This ticket is already closed or does not exist in the database."
                )
            
            # Send closure message
            embed = create_embed(
                title="Ticket Closed",
                description=f"This ticket has been closed by {interaction.user.mention}.",
                color=discord.Color.red()
            )
            
            await interaction.followup.send(embed=embed)
            
            # Disable ticket for the user
            user = interaction.guild.get_member(int(ticket.user_id))
            if user:
                try:
                    await interaction.channel.set_permissions(user, read_messages=True, send_messages=False)
                except Exception as e:
                    logger.error(f"Error updating permissions for user in closed ticket: {e}")
            
            # Send deletion warning
            await interaction.followup.send(
                "This channel will be deleted in 5 minutes. React with ❌ to cancel."
            )
            
            # Add delete confirmation button
            delete_view = DeleteTicketView(self.bot)
            delete_message = await interaction.followup.send("Delete ticket now?", view=delete_view)
            
            # Set up delayed deletion
            await asyncio.sleep(300)  # 5 minutes
            
            # Check if the channel still exists and the ticket is still closed
            channel = interaction.guild.get_channel(int(ticket.channel_id))
            if channel:
                # Check the ticket status with app context
                @with_app_context
                def check_ticket_status():
                    try:
                        from models import Ticket
                        current_ticket = Ticket.query.filter_by(
                            channel_id=str(interaction.channel.id)
                        ).first()
                        
                        if current_ticket and current_ticket.status == "closed":
                            return True
                        return False
                    except Exception as e:
                        logger.error(f"Error checking ticket status for auto-deletion: {e}")
                        return False
                
                # Delete the channel if the ticket is still closed
                if check_ticket_status():
                    try:
                        await channel.delete(reason="Ticket closed and auto-deleted after 5 minutes")
                    except Exception as e:
                        logger.error(f"Error auto-deleting ticket channel: {e}")
        
        except Exception as e:
            logger.error(f"Error in close_ticket button: {e}")
            await interaction.followup.send(
                "An error occurred while closing the ticket."
            )

class DeleteTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Delete Now", custom_id="delete_ticket", style=discord.ButtonStyle.red, emoji="⚠️")
    async def delete_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        """Button to immediately delete a ticket channel"""
        await interaction.response.defer()
        
        try:
            # Import app context function
            from app import with_app_context
            
            # Find the ticket
            @with_app_context
            def get_ticket():
                try:
                    from models import Ticket
                    ticket = Ticket.query.filter_by(
                        channel_id=str(interaction.channel.id)
                    ).first()
                    return ticket
                except Exception as e:
                    logger.error(f"Error getting ticket for deletion: {e}")
                    return None
            
            # Get the ticket
            ticket = get_ticket()
            if not ticket:
                return await interaction.followup.send(
                    "This ticket does not exist in the database."
                )
            
            # Send deletion message
            await interaction.followup.send("Deleting ticket channel...")
            
            # Delete the channel
            await asyncio.sleep(3)  # Brief delay to show the message
            await interaction.channel.delete(reason=f"Ticket deleted by {interaction.user}")
        
        except Exception as e:
            logger.error(f"Error in delete_ticket button: {e}")
            await interaction.followup.send(
                "An error occurred while deleting the ticket channel."
            )

def create_ticket_button(bot):
    """Create a ticket button view"""
    return TicketView(bot)
