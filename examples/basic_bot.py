"""
Basic Discord bot example using RustCord library
"""

import asyncio
import logging
import os
import sys
from typing import Any

# Add the parent directory to the Python path so we can import rustcord
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import rustcord
from rustcord import Client, Intents, Message

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

# Create Discord client with default intents
client = Client(intents=Intents.DEFAULT)


@client.event('ready')
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready and connected to Discord"""
    try:
        # Get information about the bot user
        me = await client.get_current_user()
        if me:
            logger.info(f'Logged in as {me.username}#{me.discriminator}')
        else:
            logger.warning('Could not retrieve user information')

        # Print list of connected guilds
        guilds = await client.get_current_guilds()
        logger.info(f'Connected to {len(guilds)} guilds:')
        for guild in guilds:
            logger.info(f'  - {guild.name} (ID: {guild.id})')

        # Check if we're in mock mode
        if hasattr(rustcord._rust, 'REAL_API') and not rustcord._rust.REAL_API:
            logger.info('Running in MOCK mode - using simulated Discord API')
            logger.info(
                "To use actual Discord API, install 'aiohttp' and 'websockets' packages"
            )
        else:
            logger.info('Connected to the real Discord API')
    except Exception as e:
        logger.error(f'Error in on_ready: {e}')
        import traceback

        logger.error(traceback.format_exc())


@client.event('message')
async def on_message(data: dict[str, Any]):
    """Called when a message is received"""
    try:
        # Extract message content
        content = data.get('content', '')

        # Create a Message object from raw data for easier handling
        message_id = data.get('id', '')
        channel_id = data.get('channel_id', '')
        author = data.get('author', {})
        author_id = author.get('id', '')
        author_username = author.get('username', '')

        message = Message(
            id=message_id,
            channel_id=channel_id,
            content=content,
            author_id=author_id,
            author_username=author_username,
            _rust_obj=None,
        )

        # Don't respond to our own messages
        try:
            # Try to get our user ID from the client
            me = await client.get_current_user()
            bot_id = me.id if me else '123456789012345678'
        except Exception as e:
            logger.warning(f'Could not retrieve bot user ID: {e}')
            # Fallback to the mock ID if we can't get the real one
            bot_id = '123456789012345678'

        if author_id == bot_id:
            return

        logger.info(f'Received message from {author_username}: {content}')

        # Check for mentions (Discord mentions look like <@USER_ID>)
        is_mentioned = False
        if f'<@{bot_id}>' in content:
            is_mentioned = True
            logger.info('Bot was mentioned in the message')

        # Simple command handler
        if content.startswith('!ping'):
            logger.info('Responding to ping command')
            await client.send_message(channel_id, 'Pong!')
        elif content.startswith('!hello'):
            await client.send_message(channel_id, f'Hello, {author_username}!')
        elif content.startswith('!info'):
            await client.send_message(
                channel_id, f"I'm a Discord bot using RustCord v{rustcord.__version__}!"
            )
        elif content.startswith('!help'):
            help_message = (
                '**RustCord Bot Commands:**\n'
                '- `!ping` - Check if the bot is responding\n'
                '- `!hello` - Get a friendly greeting\n'
                '- `!info` - Information about this bot\n'
                '- `!help` - Show this help message\n'
            )
            await client.send_message(channel_id, help_message)
        elif is_mentioned:
            # Respond to mentions
            response = f'Hello {author_username}! You mentioned me. Use `!help` to see what I can do.'
            await client.send_message(channel_id, response)
    except Exception as e:
        logger.error(f'Error in on_message handler: {e}')
        import traceback

        logger.error(traceback.format_exc())


async def main():
    # Connect to Discord
    try:
        await client.start()

        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Bot is shutting down...')
        await client.disconnect()


if __name__ == '__main__':
    # Verify token is available
    if not os.environ.get('DISCORD_TOKEN'):
        logger.error(
            'DISCORD_TOKEN environment variable is not set. Please set it before running the bot.'
        )
        sys.exit(1)
    else:
        logger.info('Discord token found, connecting to Discord...')

    # Run the bot
    asyncio.run(main())
