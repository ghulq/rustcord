#!/usr/bin/env python3
"""
Example Discord bot demonstrating slash commands with RustCord
"""

import os
import sys
import asyncio
import logging
from typing import Any

from rustcord.client import Client
from rustcord.models import CommandOption, CommandOptionType, Interaction

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('slash_command_bot')

# Create the client
client = Client()


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


# Define a simple ping command
@client.command(name='ping', description='Checks if the bot is responding')
async def ping_command(interaction: Interaction):
    """Handles the /ping command"""
    logger.info(f'Ping command used by {interaction.username}')

    # Respond to the interaction
    await interaction.respond('Pong! 🏓')


# Define a command with options
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


# Define a command with a subcommand
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
                    'description': "I'm a Discord bot using RustCord",
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
