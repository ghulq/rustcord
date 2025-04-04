"""
Example Discord bot demonstrating UI components with RustCord
"""

import os
import sys
import asyncio
import logging
from typing import Any

from rustcord import (
    Client,
    Intents,
    ApplicationCommand,
    Interaction,
    Button,
    ButtonStyle,
    ActionRow,
    SelectOption,
    SelectMenu,
    InteractionType,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('component_bot')

# Get the Discord token from environment variable
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
if not DISCORD_TOKEN:
    logger.error('DISCORD_TOKEN environment variable is not set')
    logger.error('Please set it with your bot token from the Discord Developer Portal')
    sys.exit(1)

# Create client with necessary intents
client = Client(
    intents=Intents.GUILD_MESSAGES | Intents.MESSAGE_CONTENT | Intents.GUILDS
)


# Command handlers
@client.event('ready')
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready"""
    logger.info(
        f"Connected as {data['user']['username']}#{data['user']['discriminator']}"
    )
    logger.info(f"In {len(data['guilds'])} guilds")

    # Register slash commands
    commands = [
        ApplicationCommand(
            name='buttons',
            description='Shows different button styles',
        ),
        ApplicationCommand(
            name='menu',
            description='Shows a select menu',
        ),
        ApplicationCommand(
            name='form',
            description='Shows a form with multiple components',
        ),
    ]

    # For each registered guild
    for guild in data['guilds']:
        guild_id = guild['id']
        for command in commands:
            try:
                await client.register_guild_command(guild_id, command)
                logger.info(f'Registered command {command.name} for guild {guild_id}')
            except Exception as e:
                logger.error(
                    f'Failed to register command {command.name} for guild {guild_id}: {e}'
                )


@client.event('message')
async def on_message(data: dict[str, Any]):
    """Called when a message is received"""
    # Skip messages from this bot
    if data.get('author', {}).get('bot', False):
        return

    # Create a rustcord Message object from the data directly
    message_content = data.get('content', '')
    channel_id = data.get('channel_id', '')

    # Simple ping/pong response
    if message_content.lower() == '!ping':
        await client.send_message(channel_id, 'Pong!')


@client.event('interaction')
async def on_interaction(data: dict[str, Any]) -> None:
    """Called when a slash command is invoked"""
    # Create an interaction object
    interaction = Interaction(data)

    # Only process command and component interactions
    if interaction.type not in (
        InteractionType.APPLICATION_COMMAND,
        InteractionType.MESSAGE_COMPONENT,
    ):
        return

    if interaction.type == InteractionType.APPLICATION_COMMAND:
        # Handle commands
        if interaction.command_name == 'buttons':
            # Create a set of buttons with different styles
            primary_button = Button(
                style=ButtonStyle.PRIMARY, label='Primary', custom_id='btn_primary'
            )

            secondary_button = Button(
                style=ButtonStyle.SECONDARY,
                label='Secondary',
                custom_id='btn_secondary',
            )

            success_button = Button(
                style=ButtonStyle.SUCCESS, label='Success', custom_id='btn_success'
            )

            danger_button = Button(
                style=ButtonStyle.DANGER, label='Danger', custom_id='btn_danger'
            )

            link_button = Button(
                style=ButtonStyle.LINK, label='Go to Discord', url='https://discord.com'
            )

            # First row of buttons
            row1 = ActionRow(components=[primary_button, secondary_button])
            # Second row of buttons
            row2 = ActionRow(components=[success_button, danger_button, link_button])

            await interaction.respond(
                content='Here are different button styles:', components=[row1, row2]
            )

        elif interaction.command_name == 'menu':
            # Create a select menu with options
            menu = SelectMenu(
                custom_id='color_menu',
                placeholder='Choose a color',
                options=[
                    SelectOption(
                        label='Red',
                        value='red',
                        description='A primary color',
                        emoji='🔴',
                    ),
                    SelectOption(
                        label='Green',
                        value='green',
                        description='A primary color',
                        emoji='🟢',
                    ),
                    SelectOption(
                        label='Blue',
                        value='blue',
                        description='A primary color',
                        emoji='🔵',
                    ),
                    SelectOption(
                        label='Yellow',
                        value='yellow',
                        description='A secondary color',
                        emoji='🟡',
                    ),
                    SelectOption(
                        label='Purple',
                        value='purple',
                        description='A secondary color',
                        emoji='🟣',
                    ),
                ],
                min_values=1,
                max_values=3,  # Allow selecting up to 3 options
            )

            await interaction.respond(
                content='Choose your favorite colors:', components=[menu]
            )

        elif interaction.command_name == 'form':
            # Create a more complex form with multiple components
            tier_menu = SelectMenu(
                custom_id='tier_select',
                placeholder='Select subscription tier',
                options=[
                    SelectOption(
                        label='Basic',
                        value='basic',
                        description='Basic features',
                        emoji='🥉',
                    ),
                    SelectOption(
                        label='Premium',
                        value='premium',
                        description='Premium features',
                        emoji='🥈',
                    ),
                    SelectOption(
                        label='Ultimate',
                        value='ultimate',
                        description='All features',
                        emoji='🥇',
                    ),
                ],
            )

            confirm_button = Button(
                style=ButtonStyle.SUCCESS,
                label='Confirm',
                custom_id='btn_confirm',
                emoji='✅',
            )

            cancel_button = Button(
                style=ButtonStyle.DANGER,
                label='Cancel',
                custom_id='btn_cancel',
                emoji='❌',
            )

            # Create the form with multiple rows
            await interaction.respond(
                content='Please configure your subscription options:',
                components=[
                    ActionRow(components=[tier_menu]),
                    ActionRow(components=[confirm_button, cancel_button]),
                ],
            )

    elif interaction.type == InteractionType.MESSAGE_COMPONENT:
        # Handle component interactions
        if interaction.custom_id.startswith('btn_'):
            # Handle button presses
            button_type = interaction.custom_id.replace('btn_', '')

            if button_type == 'primary':
                await interaction.respond(
                    content='You pressed the Primary button!', ephemeral=True
                )
            elif button_type == 'secondary':
                await interaction.respond(
                    content='You pressed the Secondary button!', ephemeral=True
                )
            elif button_type == 'success':
                await interaction.respond(
                    content='You pressed the Success button!', ephemeral=True
                )
            elif button_type == 'danger':
                await interaction.respond(
                    content='You pressed the Danger button!', ephemeral=True
                )
            elif button_type == 'confirm':
                await interaction.respond(
                    content='Your subscription has been confirmed!', ephemeral=True
                )
            elif button_type == 'cancel':
                await interaction.respond(
                    content='You cancelled the subscription form!', ephemeral=True
                )

        elif interaction.custom_id == 'color_menu':
            # Handle select menu interactions
            selected_colors = interaction.values
            color_str = ', '.join(selected_colors)

            await interaction.respond(
                content=f'You selected these colors: {color_str}', ephemeral=True
            )

        elif interaction.custom_id == 'tier_select':
            tier = interaction.values[0] if interaction.values else 'none'

            await interaction.respond(
                content=f'You selected the {tier.title()} tier. Use the buttons below to confirm or cancel.',
                ephemeral=True,
            )


async def main():
    """Main function"""
    try:
        # Set token env var
        os.environ['DISCORD_TOKEN'] = DISCORD_TOKEN
        # Connect to Discord
        await client.start()

        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Bot stopped by user')
    except Exception as e:
        logger.error(f'Error in main: {e}')


if __name__ == '__main__':
    asyncio.run(main())
