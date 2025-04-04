#!/usr/bin/env python3
"""
Complete Discord bot example demonstrating RustCord's functionality
"""

import os
import sys
import asyncio
import logging
from typing import Any

import rustcord
from rustcord.client import Client, Intents
from rustcord.models import CommandOption, CommandOptionType, Interaction

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('complete_bot')

# Create the client with all intents
client = Client(intents=Intents.ALL)


@client.event('ready')
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready"""
    # Get bot info
    me = await client.get_current_user()
    if me:
        logger.info(f'Logged in as {me.tag}')
    else:
        logger.info('Logged in (unable to get bot user details)')

    # Get guilds
    guilds = await client.get_current_guilds()
    if guilds:
        logger.info(f'Connected to {len(guilds)} guilds:')
        for guild in guilds:
            logger.info(f'  - {guild.name} (ID: {guild.id})')
    else:
        logger.info('Not connected to any guilds')

    logger.info('Bot is ready!')


@client.event('message')
async def on_message(data: dict[str, Any]):
    """Called when a message is received"""
    # Extract message content
    content = data.get('content', '')
    channel_id = data.get('channel_id', '')
    author = data.get('author', {})
    author_username = author.get('username', '')
    author_id = author.get('id', '')

    # Don't respond to our own messages
    try:
        me = await client.get_current_user()
        if me and author_id == me.id:
            return
    except Exception as e:
        logger.warning(f'Failed to get current user: {e}')

    logger.info(f'Received message from {author_username}: {content}')

    # Simple command handler
    if content.startswith('!ping'):
        await client.send_message(channel_id, 'Pong!')
    elif content.startswith('!help'):
        help_text = """
**Command Help**
- `!ping` - Basic ping command
- `!help` - Show this help message

**Slash Commands**
- `/ping` - Get a quick pong response
- `/echo <message>` - Echo back your message
- `/info` - Get information about the bot, server, or yourself
- `/reaction <choice>` - Example of how to use choices
        """
        await client.send_message(channel_id, help_text)


# Basic ping command
@client.command(name='ping', description='Checks if the bot is responding')
async def ping_command(interaction: Interaction):
    """Handles the /ping command"""
    logger.info(f'Ping command used by {interaction.username}')

    # Respond to the interaction
    await interaction.respond('Pong! 🏓')


# Echo command with options
@client.command(
    name='echo',
    description='Echoes your message back to you',
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name='message',
            description='The message to echo',
            required=True,
        ),
        CommandOption(
            type=CommandOptionType.BOOLEAN,
            name='ephemeral',
            description='Whether the response should be ephemeral (only visible to you)',
            required=False,
        ),
    ],
)
async def echo_command(interaction: Interaction):
    """Handles the /echo command"""
    # Get the command options
    message = interaction.get_option_value('message', '')
    ephemeral = interaction.get_option_value('ephemeral', False)

    logger.info(f'Echo command used by {interaction.username} with message: {message}')

    # Respond to the interaction
    await interaction.respond(content=f'You said: {message}', ephemeral=ephemeral)


# Info command with subcommands
@client.command(
    name='info',
    description='Get information about various things',
    options=[
        CommandOption(
            type=CommandOptionType.SUB_COMMAND,
            name='bot',
            description='Get information about the bot',
            required=False,
        ),
        CommandOption(
            type=CommandOptionType.SUB_COMMAND,
            name='server',
            description='Get information about the server',
            required=False,
        ),
        CommandOption(
            type=CommandOptionType.SUB_COMMAND,
            name='user',
            description='Get information about yourself',
            required=False,
        ),
    ],
)
async def info_command(interaction: Interaction):
    """Handles the /info command"""
    # Check which subcommand was used
    subcommand = interaction.options[0]['name'] if interaction.options else 'bot'

    logger.info(
        f'Info command used by {interaction.username} with subcommand: {subcommand}'
    )

    if subcommand == 'bot':
        # Get bot info
        me = await client.get_current_user()

        # Create an embed response
        await interaction.respond(
            content="Here's information about me:",
            embeds=[
                {
                    'title': 'Bot Information',
                    'description': f"I'm a Discord bot using RustCord v{rustcord.__version__}",
                    'color': 0x5865F2,
                    'fields': [
                        {
                            'name': 'Name',
                            'value': me.username if me else 'Unknown',
                            'inline': True,
                        },
                        {
                            'name': 'ID',
                            'value': me.id if me else 'Unknown',
                            'inline': True,
                        },
                        {'name': 'Library', 'value': 'RustCord', 'inline': True},
                    ],
                }
            ],
        )
    elif subcommand == 'server':
        # Get guild info if available
        if interaction.guild_id:
            await interaction.respond(
                content="Here's information about this server:",
                embeds=[
                    {
                        'title': 'Server Information',
                        'description': 'Information about the current Discord server',
                        'color': 0x5865F2,
                        'fields': [
                            {
                                'name': 'ID',
                                'value': interaction.guild_id,
                                'inline': True,
                            }
                        ],
                    }
                ],
            )
        else:
            await interaction.respond('This command can only be used in a server.')
    elif subcommand == 'user':
        # Get user info
        await interaction.respond(
            content="Here's information about you:",
            embeds=[
                {
                    'title': 'User Information',
                    'description': f'Information about {interaction.username}',
                    'color': 0x5865F2,
                    'fields': [
                        {
                            'name': 'Username',
                            'value': interaction.username or 'Unknown',
                            'inline': True,
                        },
                        {
                            'name': 'ID',
                            'value': interaction.user_id or 'Unknown',
                            'inline': True,
                        },
                    ],
                }
            ],
        )
    else:
        await interaction.respond(
            'Unknown subcommand. Please use /info bot, /info server, or /info user.'
        )


# Command with choices
@client.command(
    name='reaction',
    description='Choose a reaction',
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name='choice',
            description='Select your reaction',
            required=True,
            choices=[
                {'name': 'Happy', 'value': 'happy'},
                {'name': 'Sad', 'value': 'sad'},
                {'name': 'Excited', 'value': 'excited'},
                {'name': 'Confused', 'value': 'confused'},
            ],
        )
    ],
)
async def reaction_command(interaction: Interaction):
    """Handles the /reaction command"""
    choice = interaction.get_option_value('choice', '')

    logger.info(
        f'Reaction command used by {interaction.username} with choice: {choice}'
    )

    # Map choices to emojis
    reactions = {
        'happy': "😄 You're feeling happy! That's great!",
        'sad': "😢 You're feeling sad. I hope things get better soon!",
        'excited': "🎉 You're feeling excited! What's the occasion?",
        'confused': "🤔 You're feeling confused. Can I help explain something?",
    }

    response = reactions.get(choice, "I'm not sure how to react to that.")

    # Respond to the interaction
    await interaction.respond(response)


# Command that uses deferred response for "long" operations
@client.command(
    name='thinking',
    description='Makes the bot think for a few seconds before responding',
)
async def thinking_command(interaction: Interaction):
    """Handles the /thinking command - demonstrates deferred responses"""
    logger.info(f'Thinking command used by {interaction.username}')

    # First, defer the response to show a "Bot is thinking..." message
    await interaction.defer_response()

    # Simulate a long operation
    logger.info("Starting 'long' operation...")
    await asyncio.sleep(3)  # Wait for 3 seconds
    logger.info("Finished 'long' operation")

    # Now respond with the result
    # We need to use the client's edit_interaction_response method since we deferred
    await client.edit_interaction_response(
        interaction.token,
        {'content': "I've thought about it, and I've decided that Python is awesome!"},
    )


async def main():
    """Main function"""
    try:
        # Connect to Discord
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
