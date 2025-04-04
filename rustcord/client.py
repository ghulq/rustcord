"""
High-level Discord API client with Rust core
"""

import asyncio
import logging
import os
from enum import IntFlag
from typing import (
    Any,
    Optional,
    TYPE_CHECKING,
)
from collections.abc import Awaitable, Callable

from . import _rust
from .models import (
    Message,
    User,
    Channel,
    Guild,
    VoiceConnection,
    AudioPlayer,
    CommandOption,
    ApplicationCommand,
    Interaction,
    InteractionType,
    InteractionResponseType,
)

# Handle forward references to prevent circular imports
if TYPE_CHECKING:
    from .embeds import Embed

logger = logging.getLogger(__name__)


class Intents(IntFlag):
    """Discord Gateway Intents flags"""

    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_BANS = 1 << 2
    GUILD_EMOJIS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15

    # Common presets
    DEFAULT = (
        GUILDS
        | GUILD_MESSAGES
        | DIRECT_MESSAGES
        | GUILD_MESSAGE_REACTIONS
        | DIRECT_MESSAGE_REACTIONS
    )

    ALL = 32767  # All intents (2^15 - 1)
    NONE = 0  # No intents


class Client:
    """
    High-level Discord API client with Rust core

    This client provides both REST API and Gateway (WebSocket) functionality
    for interacting with the Discord API.
    """

    __slots__ = (
        'token',
        'intents',
        'shard_id',
        'shard_count',
        'rest_client',
        'gateway_client',
        'event_handlers',
        '_gateway_url',
        '_ready',
        '_command_registrations',
        '_is_sharded',
        '_autocomplete_handlers',
    )

    def __init__(
        self,
        token: Optional[str] = None,
        intents: Intents = Intents.DEFAULT,
        shard_id: int = 0,
        shard_count: int = 1,
    ):
        """
        Initialize a new Discord client

        Args:
            token: Discord bot token. If not provided, will be read from DISCORD_TOKEN env var
            intents: Gateway intents to enable
            shard_id: The shard ID for this client (0-based index)
            shard_count: Total number of shards
        """
        self.token = token or os.environ.get('DISCORD_TOKEN')
        if not self.token:
            raise ValueError(
                'No Discord token was provided. To use this library, you must either:\n'
                "1. Provide a token directly when creating the client: Client(token='your_token_here')\n"
                '2. Set the DISCORD_TOKEN environment variable\n\n'
                'You can get a bot token by creating an application at: https://discord.com/developers/applications'
            )

        # Validate shard settings
        if shard_id < 0:
            raise ValueError('shard_id must be a non-negative integer')
        if shard_count < 1:
            raise ValueError('shard_count must be at least 1')
        if shard_id >= shard_count:
            raise ValueError(
                f'shard_id ({shard_id}) must be less than shard_count ({shard_count})'
            )

        self.intents = intents
        self.shard_id = shard_id
        self.shard_count = shard_count
        self.rest_client = _rust.DiscordClient(self.token)
        self.gateway_client = _rust.GatewayClient(self.token, int(self.intents))
        self.event_handlers: dict[str, list[Callable]] = {}
        self._gateway_url = ''
        self._ready = asyncio.Event()
        self._command_registrations: list[Callable[[], Awaitable[None]]] = []
        self._is_sharded = shard_count > 1

        # Register built-in event handlers
        self.gateway_client.on('READY', self._handle_ready)
        self.gateway_client.on('INTERACTION_CREATE', self._handle_interaction)
        self.gateway_client.on('VOICE_STATE_UPDATE', self._handle_voice_state_update)
        self.gateway_client.on('VOICE_SERVER_UPDATE', self._handle_voice_server_update)

    def _handle_ready(self, data: dict[str, Any]) -> None:
        """Internal handler for the READY event"""
        logger.info(f"Connected to Discord as {data.get('user', {}).get('username')}")
        self._ready.set()

        # Call user-defined event handlers
        asyncio.create_task(self._dispatch_event('ready', data))

    def _handle_interaction(self, data: dict[str, Any]) -> None:
        """Internal handler for the INTERACTION_CREATE event"""
        logger.debug(f"Received interaction: {data.get('type')}")

        # Process the interaction
        asyncio.create_task(self.handle_interaction(data))

    def _handle_voice_state_update(self, data: dict[str, Any]) -> None:
        """Internal handler for the VOICE_STATE_UPDATE event"""
        logger.debug(
            f"Voice state update: guild_id={data.get('guild_id')}, channel_id={data.get('channel_id')}"
        )

        # Dispatch to user event handlers
        asyncio.create_task(self._dispatch_event('voice_state_update', data))

    def _handle_voice_server_update(self, data: dict[str, Any]) -> None:
        """Internal handler for the VOICE_SERVER_UPDATE event"""
        logger.debug(f"Voice server update: guild_id={data.get('guild_id')}")

        # Dispatch to user event handlers
        asyncio.create_task(self._dispatch_event('voice_server_update', data))

    async def _dispatch_event(self, event_name: str, data: dict[str, Any]) -> None:
        """Dispatch an event to all registered handlers"""
        handlers = self.event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception(f'Error in event handler for {event_name}: {e}')

    def event(self, event_name: Optional[str] = None):
        """
        Decorator to register an event handler

        Example:
            @client.event("message")
            async def on_message(message):
                print(f"Received message: {message['content']}")
        """

        def decorator(func):
            nonlocal event_name

            # Try to infer event name from function name if not provided
            actual_event_name = event_name
            if actual_event_name is None:
                if func.__name__.startswith('on_'):
                    actual_event_name = func.__name__[3:]
                else:
                    raise ValueError(
                        "Event name must be provided or function name must start with 'on_'"
                    )

            # Ensure the event_name is not None before proceeding
            if actual_event_name not in self.event_handlers:
                self.event_handlers[actual_event_name] = []

            self.event_handlers[actual_event_name].append(func)

            # Register with Rust gateway client for raw events
            if actual_event_name.upper() != actual_event_name:
                # This is a processed event, register the raw event too
                raw_event = actual_event_name.upper()

                async def raw_handler(data):
                    # Process raw event data if needed
                    await self._dispatch_event(actual_event_name, data)

                self.gateway_client.on(raw_event, raw_handler)

            return func

        return decorator

    async def connect(self):
        """Connect to Discord Gateway"""
        if not self._gateway_url:
            self._gateway_url = await self.rest_client.get_gateway_url()

        if self._is_sharded:
            logger.info(
                f'Connecting with sharding configuration: Shard {self.shard_id} of {self.shard_count}'
            )
            # Check if sharding is available
            if hasattr(self.gateway_client, 'connect_sharded'):
                await self.gateway_client.connect_sharded(
                    self._gateway_url, self.shard_id, self.shard_count
                )
            else:
                logger.warning(
                    'Sharding support not available - falling back to regular connection'
                )
                logger.warning(
                    'Some features may not work correctly in large bot deployments'
                )
                await self.gateway_client.connect(self._gateway_url)
        else:
            await self.gateway_client.connect(self._gateway_url)

        # Wait for READY event
        await self._ready.wait()

    async def disconnect(self):
        """Disconnect from Discord Gateway and clean up resources"""
        await self.gateway_client.disconnect()
        self._ready.clear()

        # Close HTTP session to prevent resource leaks
        if hasattr(self.rest_client, 'close'):
            await self.rest_client.close()

    async def start(self):
        """Start the Discord client and connect to Gateway"""
        await self.connect()

        # Register commands after connection
        for register_func in self._command_registrations:
            try:
                await register_func()
            except Exception as e:
                logger.error(f'Error registering command: {e}')

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID"""
        # Not yet implemented
        raise NotImplementedError('get_user method is not yet implemented')

    async def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID"""
        try:
            channel = await self.rest_client.get_channel(channel_id)
            return Channel(_rust_obj=channel)
        except Exception as e:
            logger.error(f'Failed to get channel {channel_id}: {e}')

    async def get_guild(self, guild_id: str) -> Optional[Guild]:
        """Get a guild by ID"""
        # Will be implemented when we have the Rust backend
        logger.warning('get_guild method is not yet fully implemented')

    async def get_current_user(self) -> Optional[User]:
        """Get the current bot user"""
        try:
            user = await self.rest_client.get_current_user()
            return User(_rust_obj=user)
        except Exception as e:
            logger.error(f'Failed to get current user: {e}')

    async def get_current_guilds(self) -> list[Guild]:
        """Get guilds for the current user"""
        try:
            rust_guilds = await self.rest_client.get_current_user_guilds()
            return [Guild(_rust_obj=guild) for guild in rust_guilds]
        except Exception as e:
            logger.error(f'Failed to get current user guilds: {e}')
            return []

    async def send_message(
        self,
        channel_id: str,
        content: Optional[str] = None,
        embed: Optional['Embed'] = None,
        embeds: Optional[list['Embed']] = None,
    ) -> Optional[Message]:
        """
        Send a message to a channel

        Args:
            channel_id: ID of the channel to send to
            content: Text content of the message
            embed: A single embed to attach to the message
            embeds: A list of embeds to attach to the message (max 10)

        Returns:
            The created message object if successful, None otherwise

        Note:
            You must provide at least one of content, embed, or embeds
        """
        # Import here to avoid circular imports
        from .embeds import Embed

        if not any([content, embed, embeds]):
            raise ValueError(
                'You must provide at least one of content, embed, or embeds'
            )

        if embed and embeds:
            raise ValueError('You cannot provide both embed and embeds parameters')

        payload = {}

        if content:
            payload['content'] = content

        # Handle embeds
        if embed and isinstance(embed, Embed):
            payload['embeds'] = [embed.to_dict()]
        elif embeds:
            # Discord has a limit of 10 embeds per message
            valid_embeds = []
            for e in embeds[:10]:
                if isinstance(e, Embed):
                    valid_embeds.append(e.to_dict())
                else:
                    raise ValueError(f'Invalid embed type: {type(e)}. Must be Embed')

            if valid_embeds:
                payload['embeds'] = valid_embeds

        try:
            # We need to extend the Rust implementation to support embeds
            # For now, we'll use a compatible approach that works with the current implementation
            if 'embeds' in payload:
                from . import _rust
                import os

                # Direct API request when using embeds since it's not yet in the Rust layer
                client = _rust.DiscordClient(os.environ.get('DISCORD_TOKEN', ''))
                endpoint = f'/channels/{channel_id}/messages'
                response = await client._api_request('POST', endpoint, json=payload)

                # Create a Message object (this is a bit of a hack until we update the Rust layer)
                msg_id = response.get('id', '')
                msg_content = response.get('content', '')
                author = response.get('author', {})
                author_id = author.get('id', '')
                author_username = author.get('username', '')

                msg = _rust.Message(
                    msg_id, channel_id, msg_content, author_id, author_username
                )
                return Message(_rust_obj=msg)
            else:
                # If no embeds, use the standard method
                # Make sure content is a string since Rust needs it
                message_content = content if content is not None else ''
                message = await self.rest_client.send_message(
                    channel_id, message_content
                )
                return Message(_rust_obj=message)
        except Exception as e:
            logger.error(f'Failed to send message to channel {channel_id}: {e}')

    async def register_global_command(
        self, command: ApplicationCommand
    ) -> Optional[dict[str, Any]]:
        """
        Register a global slash command with Discord

        Args:
            command: The command to register

        Returns:
            The registered command data from the API
        """
        try:
            result = await self.rest_client.create_global_command(command.to_dict())
            command.id = result.get('id')
            return result
        except Exception as e:
            logger.error(f'Failed to register global command {command.name}: {e}')

    async def register_guild_command(
        self, guild_id: str, command: ApplicationCommand
    ) -> Optional[dict[str, Any]]:
        """
        Register a guild-specific slash command with Discord

        Args:
            guild_id: The ID of the guild to register the command for
            command: The command to register

        Returns:
            The registered command data from the API
        """
        try:
            result = await self.rest_client.create_guild_command(
                guild_id, command.to_dict()
            )
            command.id = result.get('id')
            return result
        except Exception as e:
            logger.error(
                f'Failed to register guild command {command.name} for guild {guild_id}: {e}'
            )

    async def get_application_id(self) -> Optional[str]:
        """Get the application ID for this bot"""
        try:
            return await self.rest_client.get_application_id()
        except Exception as e:
            logger.error(f'Failed to get application ID: {e}')

    def command(
        self,
        name: str,
        description: str,
        options: Optional[list[CommandOption]] = None,
        guild_id: Optional[str] = None,
        default_member_permissions: Optional[str] = None,
        dm_permission: bool = True,
    ):
        """
        Decorator to register a slash command handler

        Example:
            @client.command("ping", "Responds with pong!")
            async def ping_command(interaction):
                await interaction.respond("Pong!")

        Args:
            name: Name of the command
            description: Description of the command
            options: Command options
            guild_id: Guild ID if this is a guild-specific command
            default_member_permissions: Permissions string (e.g. "8" for administrator)
            dm_permission: Whether the command is available in DMs (ignored for guild commands)
        """

        def decorator(func):
            # Store command info for future reference
            func._command_info = {
                'name': name,
                'description': description,
                'guild_id': guild_id,
            }

            # Create and store a mapping of option handlers for autocomplete
            if not hasattr(self, '_autocomplete_handlers'):
                self._autocomplete_handlers = {}

            autocomplete_key = f"{guild_id or 'global'}:{name}"
            if autocomplete_key not in self._autocomplete_handlers:
                self._autocomplete_handlers[autocomplete_key] = {}

            @self.event('interaction')
            async def interaction_handler(data: dict[str, Any]):
                interaction = Interaction(data)

                # Check if this is a slash command interaction with the right name
                if (
                    interaction.type == InteractionType.APPLICATION_COMMAND
                    and interaction.command_name == name
                ):
                    await func(interaction)

                # Handle autocomplete interactions for this command
                elif (
                    interaction.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE
                    and interaction.command_name == name
                    and interaction.focused_option
                    and interaction.focused_option.get('name')
                    in self._autocomplete_handlers[autocomplete_key]
                ):
                    option_name = interaction.focused_option.get('name')
                    handler = self._autocomplete_handlers[autocomplete_key][option_name]
                    await handler(interaction)

            # Register the command with Discord
            async def register_command():
                # Wait for client to be ready
                await self._ready.wait()

                command = ApplicationCommand(
                    name=name,
                    description=description,
                    options=options,
                    guild_id=guild_id,
                    default_member_permissions=default_member_permissions,
                    dm_permission=dm_permission,
                )

                if guild_id:
                    await self.register_guild_command(guild_id, command)
                else:
                    await self.register_global_command(command)

            # Store the registration task to be run after the client starts
            self._command_registrations.append(register_command)

            # Return function with added methods for permission and autocomplete
            func.autocomplete = lambda option_name: self._autocomplete_option(
                func, option_name, autocomplete_key
            )
            func.permission = lambda **kwargs: self._command_permission(func, **kwargs)

            return func

        return decorator

    def _autocomplete_option(
        self, command_func, option_name: str, autocomplete_key: str
    ):
        """
        Internal method to handle adding autocomplete handlers to commands

        This method is not intended to be called directly, but is used through
        the .autocomplete method added to command functions
        """

        def wrapper(handler_func):
            # Register this handler for this option for this command
            self._autocomplete_handlers[autocomplete_key][option_name] = handler_func
            return handler_func

        return wrapper

    def permission(self, **kwargs):
        """
        Decorator to add permission requirements to a command

        This is a shorthand for setting default_member_permissions on commands

        Example:
            @client.command("admin", "Admin-only command")
            @client.permission(administrator=True)
            async def admin_command(interaction):
                await interaction.respond("This is an admin-only command!")

        Args:
            **kwargs: Permission flags to set (administrator, manage_messages, etc.)
        """

        def decorator(func):
            return self._command_permission(func, **kwargs)

        return decorator

    def _command_permission(self, command_func, **kwargs):
        """
        Internal method to handle command permissions

        This method is not intended to be called directly, but is used through
        the .permission method added to command functions
        """
        # Store permissions in function for future use
        if not hasattr(command_func, '_permissions'):
            command_func._permissions = {}

        # Process permission kwargs
        for perm_name, perm_value in kwargs.items():
            command_func._permissions[perm_name] = perm_value

            # Special handling for common permissions
            if perm_name == 'administrator' and perm_value:
                # Administrator permission is 0x8
                command_func._permissions['_default_member_permissions'] = '8'

        return command_func

    async def handle_interaction(self, interaction_data: dict[str, Any]) -> None:
        """
        Handle an incoming interaction

        Args:
            interaction_data: Raw interaction data from the API
        """
        # Create an Interaction object from the raw data
        interaction = Interaction(interaction_data)

        # Dispatch to the interaction event handler
        await self._dispatch_event('interaction', interaction_data)

        # Automatically respond to ping interactions
        if (
            interaction.type == InteractionType.PING
            and interaction.id
            and interaction.token
        ):
            await self.create_interaction_response(
                interaction.id,
                interaction.token,
                {'type': InteractionResponseType.PONG},
            )

        # If we have specific handlers for autocomplete
        if (
            interaction.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE
            and hasattr(self, '_autocomplete_handlers')
            and interaction.command_name
            and interaction.focused_option
        ):
            # Generate the key for handler lookup
            guild_id = interaction.guild_id or 'global'
            command_name = interaction.command_name
            autocomplete_key = f'{guild_id}:{command_name}'

            # Check if we have a handler for this command and option
            if (
                autocomplete_key in self._autocomplete_handlers
                and interaction.focused_option.get('name')
                in self._autocomplete_handlers[autocomplete_key]
            ):
                logger.debug(
                    f"Handling autocomplete for {command_name}, option {interaction.focused_option.get('name')}"
                )
                option_name = interaction.focused_option.get('name')
                handler = self._autocomplete_handlers[autocomplete_key][option_name]
                try:
                    await handler(interaction)
                except Exception as e:
                    logger.error(f'Error in autocomplete handler: {e}')
                    # Send empty choices as fallback
                    await interaction.respond_autocomplete([])

    async def create_interaction_response(
        self, interaction_id: str, interaction_token: str, response_data: dict[str, Any]
    ) -> None:
        """
        Create a response to an interaction

        Args:
            interaction_id: ID of the interaction
            interaction_token: Token for the interaction
            response_data: Response data
        """
        try:
            await self.rest_client.create_interaction_response(
                interaction_id, interaction_token, response_data
            )
        except Exception as e:
            logger.error(f'Failed to create interaction response: {e}')

    async def edit_interaction_response(
        self, interaction_token: str, response_data: dict[str, Any]
    ) -> None:
        """
        Edit an original interaction response

        Args:
            interaction_token: Token for the interaction
            response_data: New response data
        """
        try:
            app_id = await self.get_application_id()
            if not app_id:
                logger.error('Cannot edit interaction response without application ID')
                return

            await self.rest_client.edit_interaction_response(
                app_id, interaction_token, response_data
            )
        except Exception as e:
            logger.error(f'Failed to edit interaction response: {e}')

    async def join_voice_channel(
        self, guild_id: str, channel_id: str
    ) -> Optional[VoiceConnection]:
        """
        Join a voice channel

        Args:
            guild_id: ID of the guild that contains the channel
            channel_id: ID of the voice channel to join

        Returns:
            VoiceConnection object if successful, None otherwise
        """
        try:
            # Check if the gateway client has voice methods
            if not hasattr(self.gateway_client, 'update_voice_state'):
                logger.warning(
                    'Voice support not available - the Rust implementation is missing'
                )
                # Create a fallback voice connection with minimal state
                return VoiceConnection(
                    guild_id=guild_id,
                    channel_id=channel_id,
                    session_id='fallback-session',
                    token='',
                    endpoint='',
                    connected=True,
                    self_mute=False,
                    self_deaf=False,
                )

            # First, update voice state to tell Discord we want to join this channel
            await self.gateway_client.update_voice_state(
                guild_id, channel_id, False, False
            )

            # Wait for voice state and server updates from Discord
            # These will come in as VOICE_STATE_UPDATE and VOICE_SERVER_UPDATE gateway events
            # The Rust layer will handle these events and create the voice connection

            # Get the voice connection from the Rust client
            if hasattr(self.gateway_client, 'get_voice_connection'):
                connection = await self.gateway_client.get_voice_connection(guild_id)
                if connection:
                    return VoiceConnection(_rust_obj=connection)

            logger.error(f'Failed to get voice connection for guild {guild_id}')
            # Fallback with minimal state
            return VoiceConnection(
                guild_id=guild_id,
                channel_id=channel_id,
                session_id='fallback-session',
                token='',
                endpoint='',
                connected=True,
                self_mute=False,
                self_deaf=False,
            )

        except Exception as e:
            logger.error(
                f'Failed to join voice channel {channel_id} in guild {guild_id}: {e}'
            )
            # Fallback
            return VoiceConnection(
                guild_id=guild_id,
                channel_id=channel_id,
                session_id='fallback-session-error',
                token='',
                endpoint='',
                connected=False,
                self_mute=False,
                self_deaf=False,
            )

    async def leave_voice_channel(self, guild_id: str) -> bool:
        """
        Leave a voice channel in a guild

        Args:
            guild_id: ID of the guild to leave voice in

        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if voice support is available
            if not hasattr(self.gateway_client, 'update_voice_state'):
                logger.warning(
                    'Voice support not available - the Rust implementation is missing'
                )
                return True  # Return success to avoid errors in the calling code

            # Passing None as the channel_id tells Discord to disconnect
            await self.gateway_client.update_voice_state(guild_id, None, False, False)
            return True
        except Exception as e:
            logger.error(f'Failed to leave voice channel in guild {guild_id}: {e}')
            return False

    async def create_audio_player(self) -> AudioPlayer:
        """
        Create a new audio player

        Returns:
            A new AudioPlayer instance
        """
        try:
            # Check if voice support is available
            if not hasattr(self.gateway_client, 'create_audio_player'):
                logger.warning(
                    'Audio player support not available - the Rust implementation is missing'
                )
                # Return a fallback audio player
                return AudioPlayer(is_playing=False, is_paused=False, volume=1.0)

            player = await self.gateway_client.create_audio_player()
            return AudioPlayer(_rust_obj=player)
        except Exception as e:
            logger.error(f'Failed to create audio player: {e}')
            # Return a fallback audio player instead of raising an exception
            return AudioPlayer(is_playing=False, is_paused=False, volume=1.0)


class InteractionResponse:
    """Helper class for creating Discord interaction responses"""

    __slots__ = ()

    @staticmethod
    def message(content: str, ephemeral: bool = False) -> dict[str, Any]:
        """
        Create a message response

        Args:
            content: Message content
            ephemeral: Whether the message should be ephemeral (only visible to the command invoker)

        Returns:
            Interaction response data
        """
        return {
            'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'content': content, 'flags': 64 if ephemeral else 0},
        }

    @staticmethod
    def deferred_message(ephemeral: bool = False) -> dict[str, Any]:
        """
        Create a deferred message response

        Args:
            ephemeral: Whether the message should be ephemeral (only visible to the command invoker)

        Returns:
            Interaction response data
        """
        return {
            'type': InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'flags': 64 if ephemeral else 0},
        }

    @staticmethod
    def embed(
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: int = 0x5865F2,
        fields: Optional[list[dict[str, Any]]] = None,
        ephemeral: bool = False,
        embed: Optional['Embed'] = None,
    ) -> dict[str, Any]:
        """
        Create an embed response

        Args:
            title: Embed title
            description: Embed description
            color: Embed color
            fields: Embed fields
            ephemeral: Whether the message should be ephemeral
            embed: A pre-built Embed object to use instead of parameters above

        Returns:
            Interaction response data
        """
        # Import here to avoid circular imports
        from .embeds import Embed

        if embed and isinstance(embed, Embed):
            # Use the provided embed object
            embed_dict = embed.to_dict()
        else:
            # Create an embed from parameters
            embed_dict = {}

            # Add color if provided (needs to be an integer)
            if color is not None:
                embed_dict['color'] = color

            if title:
                embed_dict['title'] = title

            if description:
                embed_dict['description'] = description

            if fields:
                embed_dict['fields'] = fields

        return {
            'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'embeds': [embed_dict], 'flags': 64 if ephemeral else 0},
        }
