"""
Example Discord bot demonstrating autocomplete and permission-based commands with RustCord
"""

import asyncio
import logging
from typing import Any

from rustcord import Client, Intents
from rustcord.models import CommandOption, CommandOptionType, Interaction

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create client instance
client = Client(intents=Intents.DEFAULT)

# Sample game data for autocomplete
GAMES = [
    {'name': 'Minecraft', 'id': 'game1', 'genre': 'Sandbox'},
    {'name': 'The Legend of Zelda', 'id': 'game2', 'genre': 'Adventure'},
    {'name': 'Call of Duty', 'id': 'game3', 'genre': 'FPS'},
    {'name': 'FIFA', 'id': 'game4', 'genre': 'Sports'},
    {'name': 'The Witcher 3', 'id': 'game5', 'genre': 'RPG'},
    {'name': 'Fortnite', 'id': 'game6', 'genre': 'Battle Royale'},
    {'name': 'League of Legends', 'id': 'game7', 'genre': 'MOBA'},
    {'name': 'Among Us', 'id': 'game8', 'genre': 'Party'},
    {'name': 'World of Warcraft', 'id': 'game9', 'genre': 'MMORPG'},
    {'name': 'Rocket League', 'id': 'game10', 'genre': 'Sports'},
]

# Sample roles data for autocomplete
ROLES = ['Administrator', 'Moderator', 'VIP', 'Member', 'Subscriber', 'Booster']


@client.event('ready')
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready and connected to Discord"""
    logger.info('Bot is ready and connected to Discord!')
    username = data.get('user', {}).get('username', 'Unknown')
    user_id = data.get('user', {}).get('id', 'Unknown')
    logger.info(f'Logged in as {username} (ID: {user_id})')

    # Display the invite link
    app_id = await client.get_application_id()
    if app_id:
        link = f'https://discord.com/oauth2/authorize?client_id={app_id}&scope=bot%20applications.commands&permissions=0'
        logger.info(f'Invite link: {link}')


# Autocomplete game selector command
@client.command(
    name='game',
    description='Select your favorite game',
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name='name',
            description='Game name',
            required=True,
            autocomplete=True,
        ),
        CommandOption(
            type=CommandOptionType.STRING,
            name='genre',
            description='Game genre',
            required=False,
            autocomplete=True,
        ),
    ],
)
async def game_command(interaction: Interaction):
    """Select a game with autocomplete"""
    game_name = interaction.get_option_value('name')
    genre = interaction.get_option_value('genre')

    # Find the selected game
    selected_game = None
    for game in GAMES:
        if game['name'].lower() == game_name.lower():
            selected_game = game
            break

    if selected_game:
        await interaction.respond(
            f"You selected {selected_game['name']} (ID: {selected_game['id']}, Genre: {selected_game['genre']})",
            ephemeral=True,
        )
    else:
        await interaction.respond(
            f"Game not found: {game_name}. Genre selected: {genre or 'None'}",
            ephemeral=True,
        )


# Autocomplete handler for the game name option
@game_command.autocomplete('name')
async def game_name_autocomplete(interaction: Interaction):
    """Handle autocomplete for game names"""
    # Get current input value
    current_input = ''
    if interaction.focused_option:
        current_input = interaction.focused_option.get('value', '').lower()

    # Filter games based on input
    matching_games = []
    for game in GAMES:
        if current_input in game['name'].lower():
            matching_games.append({'name': game['name'], 'value': game['name']})

    # Return results (up to 25)
    await interaction.respond_autocomplete(matching_games[:25])


# Autocomplete handler for the game genre option
@game_command.autocomplete('genre')
async def game_genre_autocomplete(interaction: Interaction):
    """Handle autocomplete for game genres"""
    # Get current input value
    current_input = ''
    if interaction.focused_option:
        current_input = interaction.focused_option.get('value', '').lower()

    # Get unique genres
    genres = set()
    for game in GAMES:
        genres.add(game['genre'])

    # Filter genres based on input
    matching_genres = []
    for genre in genres:
        if current_input in genre.lower():
            matching_genres.append({'name': genre, 'value': genre})

    # Return results
    await interaction.respond_autocomplete(matching_genres[:25])


# Admin-only command (requires administrator permission)
@client.command(
    name='admin',
    description='Admin-only command',
    default_member_permissions='8',  # Administrator permission
)
async def admin_command(interaction: Interaction):
    """Command that only administrators can use"""
    await interaction.respond(
        'This is an admin-only command! You have administrator privileges.',
        ephemeral=True,
    )


# Moderator command (requires specific permissions)
@client.command(
    name='moderate',
    description='Moderator command',
    default_member_permissions='2048',  # Permission for manage messages
)
async def moderate_command(interaction: Interaction):
    """Command for moderators with manage messages permission"""
    await interaction.respond(
        'This is a moderator command! You have permission to manage messages.',
        ephemeral=True,
    )


# Role assignment command with permission decorator
@client.command(
    name='assign_role',
    description='Assign a role to a user',
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name='role',
            description='Role to assign',
            required=True,
            autocomplete=True,
        ),
        CommandOption(
            type=CommandOptionType.USER,
            name='user',
            description='User to assign the role to',
            required=True,
        ),
    ],
)
@client.permission(administrator=True)
async def assign_role_command(interaction: Interaction):
    """Command to assign roles (admin only)"""
    role_name = interaction.get_option_value('role')
    user = interaction.get_option_value('user')

    user_name = user.get('username', 'Unknown')
    user_id = user.get('id', 'Unknown')

    await interaction.respond(
        f"Would assign role '{role_name}' to {user_name} (ID: {user_id})\n"
        f'Note: This is a demo. Actual role assignment requires Discord API integration.',
        ephemeral=True,
    )


# Autocomplete handler for role names
@assign_role_command.autocomplete('role')
async def role_autocomplete(interaction: Interaction):
    """Handle autocomplete for role names"""
    # Get current input value
    current_input = ''
    if interaction.focused_option:
        current_input = interaction.focused_option.get('value', '').lower()

    # Filter roles based on input
    matching_roles = []
    for role in ROLES:
        if current_input in role.lower():
            matching_roles.append({'name': role, 'value': role})

    # Return results
    await interaction.respond_autocomplete(matching_roles[:25])


# Run the bot
async def main():
    """Main entry point for the bot"""
    try:
        await client.start()

        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info('Bot is shutting down...')
    finally:
        # Make sure to disconnect and clean up resources
        await client.disconnect()


if __name__ == '__main__':
    asyncio.run(main())
