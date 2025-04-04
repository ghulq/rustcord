#!/usr/bin/env python3
"""
Example Discord bot demonstrating voice features with RustCord
"""

import asyncio
import logging
from typing import Any

from rustcord import (
    Client,
    Intents,
    CommandOption,
    CommandOptionType,
    Interaction,
    VoiceConnection,
    AudioPlayer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create a Discord client with voice-related intents
intents = Intents.DEFAULT | Intents.GUILD_VOICE_STATES
client = Client(intents=intents)

# Define command options
join_options = [
    CommandOption(
        type=CommandOptionType.CHANNEL,
        name='channel',
        description='The voice channel to join',
        required=True,
    )
]

play_options = [
    CommandOption(
        type=CommandOptionType.STRING,
        name='file',
        description='Path to the audio file to play',
        required=True,
    )
]

volume_options = [
    CommandOption(
        type=CommandOptionType.NUMBER,
        name='level',
        description='Volume level (0.0 to 2.0)',
        required=True,
    )
]

# Store active voice connections and players
voice_connections: dict[str, VoiceConnection] = {}
audio_players: dict[str, AudioPlayer] = {}


@client.event
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready"""
    user = data.get('user', {})
    logger.info(f"Logged in as {user.get('username')}#{user.get('discriminator')}")
    logger.info('Voice Bot is ready! Use /join, /leave, and /play commands')


@client.command('join', 'Join a voice channel', options=join_options)
async def join_command(interaction: Interaction):
    """Handles the /join command"""
    guild_id = interaction.guild_id
    if not guild_id:
        await interaction.respond(
            'This command can only be used in a server!', ephemeral=True
        )
        return

    # Get the user's voice channel (this would need to be implemented)
    # For now, we'll use a channel ID from the command option
    channel_id = interaction.get_option_value('channel')
    if not channel_id:
        await interaction.respond(
            'Please specify a voice channel to join!', ephemeral=True
        )
        return

    # Join the voice channel
    await interaction.defer_response()

    try:
        connection = await client.join_voice_channel(guild_id, channel_id)
        if connection:
            voice_connections[guild_id] = connection

            # Create an audio player for this connection
            player = await client.create_audio_player()
            audio_players[guild_id] = player

            # Attach the player to the connection
            await player.attach(connection)

            await interaction.respond('Joined voice channel successfully!')
        else:
            await interaction.respond(
                'Failed to join voice channel. Please try again.', ephemeral=True
            )
    except Exception as e:
        logger.error(f'Error joining voice channel: {e}')
        await interaction.respond(f'Error: {str(e)}', ephemeral=True)


@client.command('leave', 'Leave the current voice channel')
async def leave_command(interaction: Interaction):
    """Handles the /leave command"""
    guild_id = interaction.guild_id
    if not guild_id:
        await interaction.respond(
            'This command can only be used in a server!', ephemeral=True
        )
        return

    # Check if we're in a voice channel in this guild
    if guild_id not in voice_connections:
        await interaction.respond("I'm not in a voice channel!", ephemeral=True)
        return

    # Leave the voice channel
    await interaction.defer_response()

    try:
        # Stop audio playback if it's playing
        if guild_id in audio_players:
            player = audio_players[guild_id]
            await player.stop()
            del audio_players[guild_id]

        # Leave the voice channel
        success = await client.leave_voice_channel(guild_id)
        if success:
            del voice_connections[guild_id]
            await interaction.respond('Left voice channel successfully!')
        else:
            await interaction.respond(
                'Failed to leave voice channel. Please try again.', ephemeral=True
            )
    except Exception as e:
        logger.error(f'Error leaving voice channel: {e}')
        await interaction.respond(f'Error: {str(e)}', ephemeral=True)


@client.command('play', 'Play audio in the voice channel', options=play_options)
async def play_command(interaction: Interaction):
    """Handles the /play command"""
    guild_id = interaction.guild_id
    if not guild_id:
        await interaction.respond(
            'This command can only be used in a server!', ephemeral=True
        )
        return

    # Check if we're in a voice channel in this guild
    if guild_id not in voice_connections or guild_id not in audio_players:
        await interaction.respond(
            'I need to join a voice channel first! Use /join', ephemeral=True
        )
        return

    # Get the file to play
    file_path = interaction.get_option_value('file')
    if not file_path:
        await interaction.respond(
            'Please specify an audio file to play!', ephemeral=True
        )
        return

    # Play the audio
    await interaction.defer_response()

    try:
        player = audio_players[guild_id]

        # Stop any currently playing audio
        await player.stop()

        # Play the file
        success = await player.play_file(file_path)
        if success:
            await interaction.respond(f'Now playing: {file_path}')
        else:
            await interaction.respond(
                f'Failed to play {file_path}. Check if the file exists and is a supported format.',
                ephemeral=True,
            )
    except Exception as e:
        logger.error(f'Error playing audio: {e}')
        await interaction.respond(f'Error: {str(e)}', ephemeral=True)


@client.command('stop', 'Stop audio playback')
async def stop_command(interaction: Interaction):
    """Handles the /stop command"""
    guild_id = interaction.guild_id
    if not guild_id:
        await interaction.respond(
            'This command can only be used in a server!', ephemeral=True
        )
        return

    # Check if we have an audio player for this guild
    if guild_id not in audio_players:
        await interaction.respond('Nothing is playing!', ephemeral=True)
        return

    # Stop the audio
    try:
        player = audio_players[guild_id]
        await player.stop()
        await interaction.respond('Playback stopped!')
    except Exception as e:
        logger.error(f'Error stopping audio: {e}')
        await interaction.respond(f'Error: {str(e)}', ephemeral=True)


@client.command('volume', 'Change the playback volume', options=volume_options)
async def volume_command(interaction: Interaction):
    """Handles the /volume command"""
    guild_id = interaction.guild_id
    if not guild_id:
        await interaction.respond(
            'This command can only be used in a server!', ephemeral=True
        )
        return

    # Check if we have an audio player for this guild
    if guild_id not in audio_players:
        await interaction.respond('Nothing is playing!', ephemeral=True)
        return

    # Get the volume level (0.0 to 2.0)
    volume = interaction.get_option_value('level')
    if volume is None:
        await interaction.respond(
            'Please specify a volume level between 0.0 and 2.0!', ephemeral=True
        )
        return

    # Convert to float and clamp to valid range
    try:
        volume = float(volume)
        volume = max(0.0, min(2.0, volume))
    except ValueError:
        await interaction.respond(
            'Volume must be a number between 0.0 and 2.0!', ephemeral=True
        )
        return

    # Set the volume
    try:
        player = audio_players[guild_id]
        await player.set_volume(volume)
        await interaction.respond(f'Volume set to {volume:.1f}')
    except Exception as e:
        logger.error(f'Error setting volume: {e}')
        await interaction.respond(f'Error: {str(e)}', ephemeral=True)


async def main():
    """Main function"""
    # Start the Discord client
    await client.start()

    # Keep the bot running
    try:
        await asyncio.Future()  # Run forever
    except asyncio.CancelledError:
        pass
    finally:
        # Clean up voice connections before exiting
        for guild_id in list(voice_connections.keys()):
            try:
                await client.leave_voice_channel(guild_id)
            except:
                pass


if __name__ == '__main__':
    asyncio.run(main())
