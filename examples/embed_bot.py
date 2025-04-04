"""
Example Discord bot demonstrating rich embeds with RustCord
"""

import asyncio
import logging
from typing import Any

from rustcord import Client
from rustcord.embeds import Embed, Color

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create a client with default intents
client = Client()  # Token will be read from DISCORD_TOKEN environment variable


async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready"""
    user = data.get('user', {})
    username = user.get('username', 'Unknown')

    print(f'Logged in as {username}')
    print('Ready to send rich embeds!')


async def on_message(data: dict[str, Any]):
    """Called when a message is received"""
    content = data.get('content', '')
    author = data.get('author', {})
    channel_id = data.get('channel_id', '')

    # Skip messages from bots to prevent loops
    if author.get('bot', False):
        return

    # Simple embed example
    if content.lower() == '!embed':
        # Create a basic embed
        embed = Embed(
            title='Basic Embed Example',
            description='This is a basic embed with title and description',
            color=Color.BLUE,
        )

        await client.send_message(channel_id, embed=embed)

    # Advanced embed example
    elif content.lower() == '!advanced':
        # Create a more advanced embed with multiple features
        embed = Embed(
            title='Advanced Embed Example',
            description='This shows more embed features like fields, footer, and images',
            color=Color.GREEN,
        )

        # Add author information
        embed.set_author(
            name='RustCord Bot',
            icon_url='https://avatars.githubusercontent.com/u/6916170',
        )

        # Add fields
        embed.add_field('Field 1', 'This is a regular field', inline=False)
        embed.add_field('Inline Field 1', 'This field is inline', inline=True)
        embed.add_field('Inline Field 2', 'This field is also inline', inline=True)

        # Add an image
        embed.set_image(
            'https://s3.amazonaws.com/files.replit.com/images/Replit-logo-normal-dark.svg'
        )

        # Add a thumbnail
        embed.set_thumbnail(
            'https://discord.com/assets/1c8a54f25d101bdc607cec7228247a9a.svg'
        )

        # Add a footer
        embed.set_footer(
            text='Powered by RustCord',
            icon_url='https://www.rust-lang.org/logos/rust-logo-32x32.png',
        )

        await client.send_message(channel_id, embed=embed)

    # Multiple embeds example
    elif content.lower() == '!multi':
        # Create multiple embeds in a single message
        embed1 = Embed(
            title='First Embed', description='This is the first embed', color=Color.RED
        )

        embed2 = Embed(
            title='Second Embed',
            description='This is the second embed',
            color=Color.GOLD,
        )

        embed3 = Embed(
            title='Third Embed',
            description='This is the third embed',
            color=Color.PURPLE,
        )

        await client.send_message(
            channel_id,
            content='Here are multiple embeds:',
            embeds=[embed1, embed2, embed3],
        )

    # Help command
    elif content.lower() == '!help':
        # Create a help embed
        help_embed = Embed(
            title='Embed Bot Commands',
            description='Here are the available commands for this bot:',
            color=Color.BLURPLE,
        )

        help_embed.add_field('!embed', 'Shows a basic embed example', inline=False)
        help_embed.add_field(
            '!advanced', 'Shows an advanced embed with multiple features', inline=False
        )
        help_embed.add_field(
            '!multi', 'Shows multiple embeds in one message', inline=False
        )
        help_embed.add_field('!help', 'Shows this help message', inline=False)

        await client.send_message(channel_id, embed=help_embed)


async def main():
    """Main function"""
    # Register event handlers
    client.event('ready')(on_ready)
    client.event('message')(on_message)

    # Start the client
    await client.start()

    # Keep the bot running
    try:
        await asyncio.Future()
    except asyncio.CancelledError:
        pass
    finally:
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
