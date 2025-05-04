import discord
from datetime import datetime

def create_embed(title, description=None, color=discord.Color.blue(), timestamp=True, fields=None, footer=None, image=None, thumbnail=None, author=None):
    """
    Create a Discord embed with the specified parameters
    
    Args:
        title (str): The embed title
        description (str, optional): The embed description. Defaults to None.
        color (discord.Color, optional): The embed color. Defaults to discord.Color.blue().
        timestamp (bool, optional): Whether to include the current timestamp. Defaults to True.
        fields (list, optional): List of field dictionaries with name, value, and inline keys. Defaults to None.
        footer (dict, optional): Footer dictionary with text and icon_url keys. Defaults to None.
        image (str, optional): URL of the embed image. Defaults to None.
        thumbnail (str, optional): URL of the embed thumbnail. Defaults to None.
        author (dict, optional): Author dictionary with name, url, and icon_url keys. Defaults to None.
        
    Returns:
        discord.Embed: The created embed
    """
    embed = discord.Embed(title=title, color=color)
    
    if description:
        embed.description = description
    
    if timestamp:
        embed.timestamp = datetime.utcnow()
    
    if fields:
        for field in fields:
            embed.add_field(
                name=field.get("name", ""),
                value=field.get("value", ""),
                inline=field.get("inline", False)
            )
    
    if footer:
        embed.set_footer(
            text=footer.get("text", ""),
            icon_url=footer.get("icon_url", None)
        )
    
    if image:
        embed.set_image(url=image)
    
    if thumbnail:
        embed.set_thumbnail(url=thumbnail)
    
    if author:
        embed.set_author(
            name=author.get("name", ""),
            url=author.get("url", None),
            icon_url=author.get("icon_url", None)
        )
    
    return embed
