# RustCord

RustCord is a high-performance asynchronous Python library for interacting with the Discord API, with core functionality implemented in Rust.

## Features

- Asynchronous Python interface using `asyncio`
- High-performance Rust core for Discord API interactions
- Support for Discord REST API and Gateway (WebSocket) connections
- Resilient WebSocket connection with:
  - Automatic reconnection with exponential backoff
  - Session resuming to prevent missed events
  - Heartbeat jitter to prevent thundering herd
  - Proper connection state management
  - Comprehensive error handling and recovery
- Event-based architecture for handling Discord events
- Slash command support with command registration and interaction responses
- Support for ephemeral responses, embeds, and deferred responses
- Support for autocomplete responses
- Support for permission based interaction commands
- Minimal memory footprint and CPU usage
- Clean and intuitive Python API

## Current Status

This project is in active development. Currently:

- The Python interface has been fully designed and implemented
- A complete implementation of the Discord API client in Python is available
- Bot functionality is working with the actual Discord API
- Enhanced WebSocket connection with robust error handling and reconnection logic
- Support for Discord slash commands and interactions
- Proper command registration and interaction responses with deferred responses
- Rich embeds system for creating visually appealing messages with fields, images, and formatting
- Fully functional event dispatching system with coroutine support
- Connection state tracking and smart reconnection strategies
- Voice channel support for joining/leaving voice channels and audio playback
- UI Components (buttons, select menus, etc.) for interactive bot experiences
- Rust backend implementation is ready, providing optimized performance for core functionality

## Installation

### From PyPI

```bash
pip install rustcord
```

### For Development

Clone the repository and install in development mode:

```bash
git clone https://github.com/ghulq/rustcord.git
cd rustcord
pip install -e .
```

### Dependencies

RustCord requires the following Python packages:

```bash
pip install aiohttp websockets
```

For bot functionality, you'll need to set the `DISCORD_TOKEN` environment variable:

```bash
export DISCORD_TOKEN=your_bot_token_here
```

## Usage Examples

### Basic Bot Example

```python
import asyncio
import os
from rustcord import Client, Intents

# Create Discord client with default intents
client = Client(intents=Intents.DEFAULT)

@client.event("ready")
async def on_ready(data):
    """Called when the bot is ready and connected to Discord"""
    me = await client.get_current_user()
    print(f"Logged in as {me.username}#{me.discriminator}")
    
    # Print list of connected guilds
    guilds = await client.get_current_guilds()
    print(f"Connected to {len(guilds)} guilds:")
    for guild in guilds:
        print(f"  - {guild.name} (ID: {guild.id})")

@client.event("message")
async def on_message(data):
    """Called when a message is received"""
    content = data.get("content", "")
    author = data.get("author", {})
    author_username = author.get("username", "")
    channel_id = data.get("channel_id", "")
    
    # Don't respond to our own messages
    if author.get("id") == (await client.get_current_user()).id:
        return
    
    print(f"Received message from {author_username}: {content}")
    
    # Simple command handler
    if content.startswith("!ping"):
        await client.send_message(channel_id, "Pong!")
    elif content.startswith("!hello"):
        await client.send_message(channel_id, f"Hello, {author_username}!")

async def main():
    # Connect to Discord
    try:
        await client.start()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Bot is shutting down...")
        await client.disconnect()

if __name__ == "__main__":
    # Get token from environment variable
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("Please set the DISCORD_TOKEN environment variable")
        exit(1)
    
    # Run the bot
    asyncio.run(main())
```

### Rich Embed Bot Example

```python
import asyncio
import os
from typing import Any
from rustcord import Client, Intents
from rustcord.embeds import Embed, Color

# Create Discord client
client = Client(intents=Intents.DEFAULT)

@client.event("ready")
async def on_ready(data: dict[str, Any]):
    """Called when the bot is ready"""
    me = await client.get_current_user()
    print(f"Logged in as {me.username}")
    print("Ready to send rich embeds!")

@client.event("message")
async def on_message(data: dict[str, Any]):
    """Called when a message is received"""
    content = data.get("content", "")
    author = data.get("author", {})
    author_id = author.get("id", "")
    channel_id = data.get("channel_id", "")
    
    # Don't respond to our own messages
    if author_id == (await client.get_current_user()).id:
        return
    
    # Send info embed
    if content == "!info":
        # Create a rich embed with various features
        embed = Embed(
            title="RustCord Information",
            description="A high-performance Discord API library with Rust core",
            color=Color.BLURPLE
        )
        
        # Add author information
        embed.set_author(
            name=author.get("username", "User"),
            icon_url=f"https://cdn.discordapp.com/avatars/{author_id}/{author.get('avatar')}.png"
        )
        
        # Add fields - some inline, some not
        embed.add_field("Version", "1.0.0", inline=True)
        embed.add_field("Library", "RustCord", inline=True)
        embed.add_field("Language", "Python + Rust", inline=True)
        embed.add_field("Features", "• Fast WebSocket connections\n• Rich embeds\n• Slash commands", inline=False)
        
        # Add footer
        embed.set_footer(text="Powered by RustCord", icon_url="https://example.com/icon.png")
        
        # Add timestamp
        embed.set_timestamp()
        
        # Send the embed
        await client.send_message(channel_id, embed=embed)
    
    # Send multiple embeds
    elif content == "!colors":
        # Create multiple embeds to demonstrate colors
        embeds = [
            Embed(title="Red Embed", description="This embed is red", color=Color.RED),
            Embed(title="Green Embed", description="This embed is green", color=Color.GREEN),
            Embed(title="Blue Embed", description="This embed is blue", color=Color.BLUE),
            Embed(title="Custom Color", description="This embed has a custom purple color", 
                  color=Color.from_rgb(128, 0, 255))
        ]
        
        # Send multiple embeds in one message
        await client.send_message(channel_id, content="Here are some colored embeds:", embeds=embeds)

async def main():
    """Main function"""
    try:
        await client.start()
        
        # Keep the bot running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Bot is shutting down...")
        await client.disconnect()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
```

### Slash Commands Example

```python
import asyncio
import os
from rustcord import Client
from rustcord.models import CommandOption, CommandOptionType, Interaction

# Create Discord client
client = Client()

@client.event("ready")
async def on_ready(data):
    """Called when the bot is ready"""
    me = await client.get_current_user()
    print(f"Logged in as {me.tag}")
    print("Bot is ready!")

# Define a simple ping command
@client.command(
    name="ping",
    description="Checks if the bot is responding"
)
async def ping_command(interaction: Interaction):
    """Handles the /ping command"""
    await interaction.respond("Pong! 🏓")

# Define a command with options
@client.command(
    name="echo",
    description="Echoes your message back to you",
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name="message",
            description="The message to echo",
            required=True
        ),
        CommandOption(
            type=CommandOptionType.BOOLEAN,
            name="ephemeral",
            description="Whether the response should be ephemeral (only visible to you)",
            required=False
        )
    ]
)
async def echo_command(interaction: Interaction):
    """Handles the /echo command"""
    # Get the command options
    message = interaction.get_option_value("message", "")
    ephemeral = interaction.get_option_value("ephemeral", False)
    
    # Respond to the interaction
    await interaction.respond(
        content=f"You said: {message}",
        ephemeral=ephemeral
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
        print("Bot is shutting down...")
        await client.disconnect()

if __name__ == "__main__":
    # Run the bot
    asyncio.run(main())
```

## Advanced Features

The library currently supports:

- Slash Commands & Discord Interactions API
- Command Registration (both global and guild-specific)
- Command Options (arguments for slash commands)
- Subcommands and option choices
- Ephemeral Responses (responses only visible to the command user)
- Rich Embeds with fields, images, colors, and formatting
- Deferred Responses (for commands that take longer to process)
- Autocompletion for Interaction Options
- Permission based Interaction Commands
- Voice Channels support:
  - Joining and leaving voice channels
  - Audio playback from files
  - Volume control
- Sharding support for scaling bots to large guild counts

Coming soon:

- Type-safe API interfaces with Rust validation
- Modal Forms
- Voice recording and streaming

## Documentation

### Connection Architecture

RustCord's WebSocket connection to the Discord Gateway implements several important reliability features:

1. **Connection State Management**
   - Tracks the WebSocket connection through multiple states (Disconnected, Connecting, Connected, Reconnecting, Resuming, Identifying)
   - Safe state transitions to prevent race conditions with mutex locks

2. **Automatic Reconnection**
   - Exponential backoff strategy for reconnection attempts
   - Jitter added to prevent thundering herd problems
   - Configurable max reconnection attempts and backoff limits

3. **Session Resuming**
   - Maintains session information to resume instead of creating new sessions
   - Properly tracks sequence numbers to prevent missed events
   - Handles Discord's INVALID_SESSION events appropriately

4. **Heartbeat Management**
   - Immediate first heartbeat to quickly establish connection
   - Automatic heartbeat acknowledgement tracking with timeout detection
   - Jitter added to heartbeat timing to distribute load

5. **Error Recovery**
   - Comprehensive error handling for all Gateway events
   - Automatic recovery from common errors
   - Special handling for fatal connection errors (authentication failures, etc.)
   - Connection timeouts to detect stalled connections

### Main Components

#### Client

The `Client` class is the main entry point for interacting with Discord:

```python
from rustcord import Client, Intents

# Create a client with specific intents
client = Client(intents=Intents.DEFAULT)  

# Register event handlers
@client.event("ready")
async def on_ready(data):
    print("Bot is ready!")

# Start the client
await client.start()
```

#### Intents

Discord requires specifying which events your bot wants to receive through Gateway Intents:

```python
from rustcord import Intents

# Use predefined intent groups
client = Client(intents=Intents.DEFAULT)  # Common intents for most bots
client = Client(intents=Intents.ALL)      # All intents (privileged intents require approval)
client = Client(intents=Intents.NONE)     # No intents

# Or combine specific intents
intents = Intents.GUILDS | Intents.GUILD_MESSAGES | Intents.DIRECT_MESSAGES
client = Client(intents=intents)
```

#### Events

Register handlers for Discord Gateway events:

```python
@client.event("ready")
async def on_ready(data):
    print("Bot is ready!")

@client.event("message")
async def on_message(data):
    print(f"Received message: {data.get('content')}")
```

#### Slash Commands

Register and handle slash commands:

```python
@client.command(
    name="ping",
    description="Checks if the bot is responding"
)
async def ping_command(interaction):
    await interaction.respond("Pong!")
```

Commands with options:

```python
@client.command(
    name="echo",
    description="Echoes your message",
    options=[
        CommandOption(
            type=CommandOptionType.STRING,
            name="message",
            description="The message to echo",
            required=True
        )
    ]
)
async def echo_command(interaction):
    message = interaction.get_option_value("message")
    await interaction.respond(f"You said: {message}")
```

Guild-specific commands:

```python
@client.command(
    name="guild_only",
    description="This command only works in a specific guild",
    guild_id="123456789012345678"  # Your guild ID here
)
async def guild_command(interaction):
    await interaction.respond("This command only works in this server!")
```

#### Rich Embeds

Create rich embed messages with various formatting options:

```python
from rustcord import Client
from rustcord.embeds import Embed, Color

# Create a simple embed
embed = Embed(
    title="Hello, world!",
    description="This is a rich embed message",
    color=Color.BLUE
)

# Add fields
embed.add_field("Regular Field", "This is a regular field", inline=False)
embed.add_field("Inline Field 1", "This is inline", inline=True)
embed.add_field("Inline Field 2", "This is also inline", inline=True)

# Add author information
embed.set_author(
    name="RustCord Bot",
    icon_url="https://example.com/icon.png"
)

# Add footer
embed.set_footer(
    text="Powered by RustCord",
    icon_url="https://example.com/footer_icon.png"
)

# Add images
embed.set_thumbnail("https://example.com/thumbnail.png")
embed.set_image("https://example.com/image.png")

# Send the embed
await client.send_message(channel_id, embed=embed)

# Send multiple embeds
embeds = [
    Embed(title="First Embed", color=Color.RED),
    Embed(title="Second Embed", color=Color.GREEN)
]
await client.send_message(channel_id, embeds=embeds)

# Color utilities
custom_color = Color.from_rgb(255, 0, 255)  # Creates purple color
```

#### Interaction Responses

Respond to interactions in various ways:

```python
# Basic text response
await interaction.respond("Hello!")

# Ephemeral response (only visible to the command user)
await interaction.respond("This is private", ephemeral=True)

# Response with embeds using the Embed class
from rustcord.embeds import Embed, Color

embed = Embed(
    title="Embed Title",
    description="This is an embed",
    color=Color.BLURPLE
)
embed.add_field("Field 1", "Value 1", inline=True)
embed.add_field("Field 2", "Value 2", inline=True)

await interaction.respond(embed=embed)

# Deferred response (for commands that take time to process)
await interaction.defer_response()
# ... do some work ...
await client.edit_interaction_response(
    interaction.token,
    {"content": "Here's the result after processing!"}
)
```

#### Voice Features

Connect to voice channels and play audio:

```python
from rustcord import Client, Intents
from rustcord.models import VoiceConnection, AudioPlayer

# Create Discord client with voice intents
intents = Intents.DEFAULT | Intents.GUILD_VOICE_STATES
client = Client(intents=intents)

# Store active voice connections and players
voice_connections = {}
audio_players = {}

@client.command("join", "Join a voice channel")
async def join_command(interaction):
    guild_id = interaction.guild_id
    channel_id = interaction.get_option_value("channel")
    
    # Join the voice channel
    connection = await client.join_voice_channel(guild_id, channel_id)
    if connection:
        voice_connections[guild_id] = connection
        
        # Create an audio player for this connection
        player = await client.create_audio_player()
        audio_players[guild_id] = player
        
        # Attach the player to the connection
        await player.attach(connection)
        
        await interaction.respond("Joined voice channel successfully!")

@client.command("play", "Play audio in the voice channel")
async def play_command(interaction):
    guild_id = interaction.guild_id
    file_path = interaction.get_option_value("file")
    
    # Check if we're in a voice channel
    if guild_id not in audio_players:
        await interaction.respond("I need to join a voice channel first!")
        return
    
    # Play audio
    player = audio_players[guild_id]
    success = await player.play_file(file_path)
    
    if success:
        await interaction.respond(f"Now playing: {file_path}")
    else:
        await interaction.respond("Failed to play the file.")

@client.command("leave", "Leave the voice channel")
async def leave_command(interaction):
    guild_id = interaction.guild_id
    
    # Leave the voice channel
    if guild_id in voice_connections:
        # Stop any audio playback
        if guild_id in audio_players:
            await audio_players[guild_id].stop()
        
        # Leave the channel
        success = await client.leave_voice_channel(guild_id)
        if success:
            await interaction.respond("Left voice channel!")
```

#### Sharding

For bots in large numbers of guilds (approaching Discord's limit of 2500 guilds per connection), sharding is necessary:

```python
from rustcord import Client, Intents

# Create a sharded client
client = Client(
    intents=Intents.DEFAULT,
    shard_id=0,     # Current shard ID (0-based)
    shard_count=2   # Total number of shards
)

# The client will only receive events for guilds that match:
# guild_id % shard_count = shard_id

# Multiple shards can be run in separate processes
# For example, to run shard 1 of 2:
client_shard1 = Client(
    intents=Intents.DEFAULT,
    shard_id=1,
    shard_count=2
)

# Rest of the code is the same as a non-sharded bot
@client.event("ready")
async def on_ready(data):
    print(f"Shard 0 is ready!")

@client_shard1.event("ready")
async def on_ready_shard1(data):
    print(f"Shard 1 is ready!")
```
