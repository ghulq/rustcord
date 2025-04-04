"""
Python implementation of rustcord

This module provides a bridge to the Discord API using aiohttp and websockets.
It serves as the implementation layer for Discord API interactions.
"""

import asyncio
import json
import logging
import random
import time
import sys
from enum import Enum
from typing import Any, Optional
from collections.abc import Callable

# Set up logging first
__version__ = '0.1.3-py'
logger = logging.getLogger(__name__)

# Import required libraries
try:
    import aiohttp
    import websockets

    # We have the required dependencies, so use the real Discord API
    REAL_API = True
    logger.info('Using real Discord API with aiohttp and websockets')
except ImportError:
    # Fall back to mock mode if dependencies aren't available
    REAL_API = False
    logger.warning('aiohttp or websockets not found, using mock API mode')
    logger.warning('Install aiohttp and websockets for full functionality')


# Mock Discord data models
class Message:
    __slots__ = ('id', 'channel_id', 'content', 'author_id', 'author_username')

    def __init__(
        self,
        id: str,
        channel_id: str,
        content: str,
        author_id: str,
        author_username: str,
    ):
        self.id = id
        self.channel_id = channel_id
        self.content = content
        self.author_id = author_id
        self.author_username = author_username

    def __str__(self):
        return f'<Message id={self.id} content={self.content}>'


class User:
    __slots__ = ('id', 'username', 'discriminator', 'bot')

    def __init__(self, id: str, username: str, discriminator: str, bot: bool = False):
        self.id = id
        self.username = username
        self.discriminator = discriminator
        self.bot = bot

    def __str__(self):
        return f'<User id={self.id} username={self.username}>'


class Channel:
    __slots__ = ('id', 'name', 'channel_type', 'guild_id')

    def __init__(
        self, id: str, name: str, channel_type: int, guild_id: Optional[str] = None
    ):
        self.id = id
        self.name = name
        self.channel_type = channel_type
        self.guild_id = guild_id

    def __str__(self):
        return f'<Channel id={self.id} name={self.name}>'


class Guild:
    __slots__ = ('id', 'name', 'owner_id')

    def __init__(self, id: str, name: str, owner_id: str):
        self.id = id
        self.name = name
        self.owner_id = owner_id

    def __str__(self):
        return f'<Guild id={self.id} name={self.name}>'


class DiscordError(Exception):
    __slots__ = ('message', 'error_type')

    def __init__(self, message: str, error_type: str):
        self.message = message
        self.error_type = error_type
        super().__init__(self.message)

    def __str__(self):
        return f'DiscordError[{self.error_type}]: {self.message}'


class GatewayError(Exception):
    """Error raised for Discord Gateway connection issues"""

    __slots__ = ('message', 'code')

    def __init__(self, message: str, code=None):
        self.message = message
        self.code = code
        super().__init__(self.message)

    def __str__(self):
        if self.code:
            return f'GatewayError[{self.code}]: {self.message}'
        return f'GatewayError: {self.message}'


# Discord API Client
class DiscordClient:
    __slots__ = (
        'token',
        'api_base',
        'headers',
        'session',
        '_bot_user',
        '_guilds',
        '_channels',
        'application_id',
    )

    def __init__(self, token: str):
        if not token:
            raise ValueError(
                'No Discord token was provided. To use this library, you must either:\n'
                "1. Provide a token directly when creating the client: Client(token='your_token_here')\n"
                '2. Set the DISCORD_TOKEN environment variable\n\n'
                'You can get a bot token by creating an application at: https://discord.com/developers/applications'
            )

        self.token = token
        self.api_base = 'https://discord.com/api/v10'
        self.headers = {
            'Authorization': f'Bot {self.token}',
            'User-Agent': 'RustCord/0.1.3',
            'Content-Type': 'application/json',
        }
        self.session = None
        self._bot_user = None
        self._guilds = {}
        self._channels = {}
        self.application_id = None  # Will be populated when we get user info

    async def _ensure_session(self):
        """Ensure we have an active HTTP session"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def close(self):
        """Close the HTTP session and clean up resources"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def _api_request(self, method: str, endpoint: str, **kwargs):
        """Make an API request to Discord"""
        if not REAL_API:
            logger.warning(f'Cannot make API request to {endpoint}, using mock data')
            return {}

        await self._ensure_session()
        url = f'{self.api_base}{endpoint}'

        try:
            async with self.session.request(
                method, url, headers=self.headers, **kwargs
            ) as resp:
                if resp.status >= 400:
                    error_text = await resp.text()
                    logger.error(f'Discord API error: {resp.status} - {error_text}')
                    raise DiscordError(
                        f'API request failed: {error_text}', f'HTTP_{resp.status}'
                    )

                return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f'HTTP request error: {e}')
            raise DiscordError(f'HTTP request failed: {e}', 'HTTP_ERROR')

    async def send_message(self, channel_id: str, content: str):
        """Send a message to a channel"""
        if not REAL_API:
            # Mock implementation
            msg_id = str(int(time.time() * 1000))
            bot_user = await self.get_current_user()
            message = Message(
                id=msg_id,
                channel_id=channel_id,
                content=content,
                author_id=bot_user.id,
                author_username=bot_user.username,
            )
            logger.debug(f'[MOCK] Sent message: {content} to channel {channel_id}')
            return message

        data = {'content': content}
        response = await self._api_request(
            'POST', f'/channels/{channel_id}/messages', json=data
        )

        message = Message(
            id=response['id'],
            channel_id=channel_id,
            content=content,
            author_id=response['author']['id'],
            author_username=response['author']['username'],
        )

        logger.debug(f'Sent message: {content} to channel {channel_id}')
        return message

    async def get_channel(self, channel_id: str):
        """Get a channel by ID"""
        if not REAL_API or channel_id in self._channels:
            # Return cached or mock channel
            if channel_id in self._channels:
                return self._channels[channel_id]
            return Channel(id=channel_id, name='unknown-channel', channel_type=0)

        response = await self._api_request('GET', f'/channels/{channel_id}')

        channel = Channel(
            id=response['id'],
            name=response.get('name', 'Direct Message'),
            channel_type=response['type'],
            guild_id=response.get('guild_id'),
        )

        self._channels[channel_id] = channel
        return channel

    async def get_current_user(self):
        """Get the current bot user"""
        if not REAL_API or self._bot_user is not None:
            # Return cached or mock user
            if self._bot_user is not None:
                return self._bot_user
            return User(
                id='123456789012345678',
                username='RustCordBot',
                discriminator='0000',
                bot=True,
            )

        response = await self._api_request('GET', '/users/@me')

        user = User(
            id=response['id'],
            username=response['username'],
            discriminator=response.get('discriminator', '0'),
            bot=response.get('bot', True),
        )

        self._bot_user = user
        return user

    async def get_current_user_guilds(self):
        """Get guilds for the current user"""
        if not REAL_API and not self._guilds:
            # Return mock guilds
            return [
                Guild(
                    id='111222333444555666',
                    name='Test Server',
                    owner_id='123123123123123123',
                )
            ]

        if not self._guilds:
            response = await self._api_request('GET', '/users/@me/guilds')

            for guild_data in response:
                guild = Guild(
                    id=guild_data['id'],
                    name=guild_data['name'],
                    owner_id=guild_data.get('owner_id', 'unknown'),
                )
                self._guilds[guild.id] = guild

        return list(self._guilds.values())

    async def get_gateway_url(self):
        """Get the gateway URL for websocket connections"""
        try:
            response = await self._api_request('GET', '/gateway')
            return f"{response['url']}/?v=10&encoding=json"
        except Exception as e:
            print(f'Error getting gateway URL: {e}')
            # Default Discord gateway URL as fallback
            return 'wss://gateway.discord.gg/?v=10&encoding=json'

    async def get_application_id(self):
        """Get the application ID for the bot"""
        if self.application_id:
            return self.application_id

        # Get the current user
        user = await self.get_current_user()
        if not user:
            logger.error('Failed to get current user to determine application ID')
            return

        # Try to fetch from the API
        try:
            response = await self._api_request('GET', '/oauth2/applications/@me')
            self.application_id = response['id']
            return self.application_id
        except Exception as e:
            logger.warning(f'Failed to get application ID from API: {e}')
            # Fall back to user ID if we can't get the application ID
            logger.info('Falling back to user ID as application ID')
            self.application_id = user.id
            return user.id

    async def create_global_command(self, command_data: dict[str, Any]):
        """
        Register a global slash command with Discord

        Args:
            command_data: Command data in the format required by Discord API
        """
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command registration', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info(f"[MOCK] Registered global command: {command_data['name']}")
            return {'id': '123456789', **command_data}

        response = await self._api_request(
            'POST', f'/applications/{app_id}/commands', json=command_data
        )

        logger.info(f"Registered global command: {command_data['name']}")
        return response

    async def create_guild_command(self, guild_id: str, command_data: dict[str, Any]):
        """
        Register a guild-specific slash command with Discord

        Args:
            guild_id: ID of the guild to register the command for
            command_data: Command data in the format required by Discord API
        """
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command registration', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info(
                f"[MOCK] Registered guild command: {command_data['name']} for guild {guild_id}"
            )
            return {'id': '123456789', **command_data}

        response = await self._api_request(
            'POST',
            f'/applications/{app_id}/guilds/{guild_id}/commands',
            json=command_data,
        )

        logger.info(
            f"Registered guild command: {command_data['name']} for guild {guild_id}"
        )
        return response

    async def get_global_commands(self):
        """Get all global slash commands for this application"""
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command retrieval', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info('[MOCK] Retrieved global commands')
            return []

        response = await self._api_request('GET', f'/applications/{app_id}/commands')
        return response

    async def get_guild_commands(self, guild_id: str):
        """Get all guild-specific slash commands for this application"""
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command retrieval', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info(f'[MOCK] Retrieved guild commands for guild {guild_id}')
            return []

        response = await self._api_request(
            'GET', f'/applications/{app_id}/guilds/{guild_id}/commands'
        )
        return response

    async def delete_global_command(self, command_id: str):
        """Delete a global slash command"""
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command deletion', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info(f'[MOCK] Deleted global command: {command_id}')
            return

        await self._api_request(
            'DELETE', f'/applications/{app_id}/commands/{command_id}'
        )
        logger.info(f'Deleted global command: {command_id}')

    async def delete_guild_command(self, guild_id: str, command_id: str):
        """Delete a guild-specific slash command"""
        app_id = await self.get_application_id()
        if not app_id:
            raise DiscordError(
                'Failed to get application ID for command deletion', 'APP_ID_ERROR'
            )

        if not REAL_API:
            logger.info(
                f'[MOCK] Deleted guild command: {command_id} from guild {guild_id}'
            )
            return

        await self._api_request(
            'DELETE', f'/applications/{app_id}/guilds/{guild_id}/commands/{command_id}'
        )
        logger.info(f'Deleted guild command: {command_id} from guild {guild_id}')

    async def create_interaction_response(
        self, interaction_id: str, interaction_token: str, response_data: dict[str, Any]
    ):
        """
        Create a response to an interaction

        Args:
            interaction_id: ID of the interaction to respond to
            interaction_token: Token for the interaction
            response_data: Response data in the format required by Discord API
        """
        if not REAL_API:
            logger.info(f'[MOCK] Created interaction response for {interaction_id}')
            return

        await self._api_request(
            'POST',
            f'/interactions/{interaction_id}/{interaction_token}/callback',
            json=response_data,
        )

        logger.debug(f'Created interaction response for {interaction_id}')

    async def edit_interaction_response(
        self, application_id: str, interaction_token: str, response_data: dict[str, Any]
    ):
        """
        Edit an original interaction response

        Args:
            application_id: Application ID
            interaction_token: Token for the interaction
            response_data: New response data
        """
        if not REAL_API:
            logger.info(
                f'[MOCK] Edited interaction response for application {application_id}'
            )
            return

        await self._api_request(
            'PATCH',
            f'/webhooks/{application_id}/{interaction_token}/messages/@original',
            json=response_data,
        )

        logger.debug('Edited interaction response')


# Discord Gateway (WebSocket) client
class ConnectionState(Enum):
    """Connection states for WebSocket lifecycle management"""

    DISCONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2
    RECONNECTING = 3
    RESUMING = 4
    IDENTIFYING = 5


class GatewayClient:
    __slots__ = (
        'token',
        'intents',
        'state',
        'event_callbacks',
        'gateway_url',
        '_event_task',
        '_heartbeat_task',
        '_reconnect_task',
        '_ws',
        '_session_id',
        '_sequence',
        '_heartbeat_interval',
        '_last_heartbeat_ack',
        '_heartbeat_jitter',
        '_reconnect_attempts',
        '_max_reconnect_attempts',
        '_close_code',
        '_base_backoff',
        '_max_backoff',
        '_connection_lock',
    )

    def __init__(self, token: str, intents: int):
        if not token:
            raise ValueError(
                'No Discord token was provided. To use this library, you must either:\n'
                "1. Provide a token directly when creating the client: Client(token='your_token_here')\n"
                '2. Set the DISCORD_TOKEN environment variable\n\n'
                'You can get a bot token by creating an application at: https://discord.com/developers/applications'
            )

        self.token = token
        self.intents = intents
        self.state = ConnectionState.DISCONNECTED
        self.event_callbacks = {}
        self.gateway_url = None

        # Tasks
        self._event_task = None
        self._heartbeat_task = None
        self._reconnect_task = None

        # WebSocket connection
        self._ws = None

        # Connection state
        self._session_id = None
        self._sequence = None
        self._heartbeat_interval = 30000  # Default interval in ms
        self._last_heartbeat_ack = True  # Whether last heartbeat was acknowledged
        self._heartbeat_jitter = 0  # Random jitter for heartbeat timing

        # Reconnection state
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._close_code = None
        self._base_backoff = 1.0  # Starting backoff in seconds
        self._max_backoff = 60.0  # Maximum backoff in seconds

        # Gateway connection mutex to prevent parallel connection attempts
        self._connection_lock = asyncio.Lock()

    def on(self, event_name: str, callback: Callable):
        """Register a callback for an event"""
        self.event_callbacks[event_name] = callback

    async def connect(self, gateway_url: str):
        """Connect to the Discord Gateway"""
        logger.info(f'Connecting to Gateway at {gateway_url}')

        # Store the gateway URL for reconnects
        self.gateway_url = gateway_url

        # Check if we're in mock mode
        if hasattr(sys.modules[__name__], 'REAL_API') and not REAL_API:
            logger.warning('Using mock mode for Gateway connection')
            self.state = ConnectionState.CONNECTED

            # Simulate the connection and READY event for mock mode
            async def _simulate_events():
                # Simulate a READY event
                await asyncio.sleep(0.5)
                ready_data = {
                    'v': 10,
                    'user': {
                        'id': '123456789012345678',
                        'username': 'RustCordBot',
                        'discriminator': '0000',
                        'bot': True,
                    },
                    'guilds': [
                        {
                            'id': '111222333444555666',
                            'name': 'Test Server',
                            'owner_id': '123123123123123123',
                        }
                    ],
                    'session_id': 'abc123def456',
                }

                if 'READY' in self.event_callbacks:
                    try:
                        self.event_callbacks['READY'](ready_data)
                    except Exception as e:
                        logger.error(f'Error in READY event handler: {e}')

            # Start the event simulation in the background
            self._event_task = asyncio.create_task(_simulate_events())
            return

        # Use a lock to prevent multiple connection attempts
        async with self._connection_lock:
            # Reset reconnection state
            self._reconnect_attempts = 0
            self._close_code = None

            # Attempt the connection
            await self._connect_and_identify()

    async def _connect_and_identify(self):
        """Connect to the Gateway and identify or resume the session"""
        if self.state in (
            ConnectionState.CONNECTED,
            ConnectionState.IDENTIFYING,
            ConnectionState.RESUMING,
        ):
            logger.debug(f'Already in state {self.state}, not reconnecting')
            return

        try:
            self.state = ConnectionState.CONNECTING
            logger.debug(f'Connecting to Gateway: {self.gateway_url}')

            # Calculate jitter for heartbeat to prevent thundering herd
            self._heartbeat_jitter = random.uniform(-0.1, 0.1)  # ±10% jitter

            # Connect to the Discord Gateway
            self._ws = await websockets.connect(
                self.gateway_url,
                # Add proper connection timeout
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                # Add compression
                compression=None,  # None means no compression
                # Add SSL context
                ssl=True,
            )

            # Handle the initial hello message to get heartbeat interval
            hello_msg = await self._ws.recv()
            hello_data = json.loads(hello_msg)

            if hello_data['op'] == 10:  # HELLO
                self._heartbeat_interval = hello_data['d']['heartbeat_interval']
                self._last_heartbeat_ack = True

                # Try to resume if we have a session
                if self._session_id and self._sequence:
                    await self._send_resume()
                else:
                    await self._send_identify()

                # Start the heartbeat task
                if self._heartbeat_task and not self._heartbeat_task.done():
                    self._heartbeat_task.cancel()
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                # Start the event handling loop
                if self._event_task and not self._event_task.done():
                    self._event_task.cancel()
                self._event_task = asyncio.create_task(self._event_loop())

                # Connection successful, set state to IDENTIFYING
                # (will be changed to CONNECTED when READY is received)
                self.state = ConnectionState.IDENTIFYING
            else:
                logger.error(f'Unexpected initial message: {hello_data}')
                await self.disconnect()
                raise GatewayError('Unexpected initial Gateway message')
        except Exception as e:
            logger.error(f'Error connecting to gateway: {e}')
            self.state = ConnectionState.DISCONNECTED
            if self._ws:
                await self._ws.close()
            self._ws = None

            # Only try to reconnect if it wasn't an intentional disconnect
            if self._close_code != 1000:
                await self._schedule_reconnect()
            raise

    async def _send_identify(self):
        """Send IDENTIFY payload to Discord Gateway"""
        logger.debug('Sending IDENTIFY payload')
        self.state = ConnectionState.IDENTIFYING

        identify_payload = {
            'op': 2,  # IDENTIFY opcode
            'd': {
                'token': self.token,
                'properties': {
                    '$os': 'linux',
                    '$browser': 'rustcord',
                    '$device': 'rustcord',
                },
                'intents': self.intents,
                'compress': False,
            },
        }

        await self._ws.send(json.dumps(identify_payload))

    async def _send_resume(self):
        """Send RESUME payload to Discord Gateway"""
        logger.info(f'Attempting to resume session {self._session_id}')
        self.state = ConnectionState.RESUMING

        resume_payload = {
            'op': 6,  # RESUME opcode
            'd': {
                'token': self.token,
                'session_id': self._session_id,
                'seq': self._sequence,
            },
        }

        await self._ws.send(json.dumps(resume_payload))

    async def _heartbeat_loop(self):
        """Send heartbeats to keep the connection alive with jitter"""
        try:
            # Send initial heartbeat immediately
            await self._send_heartbeat()

            while self.state in (
                ConnectionState.CONNECTED,
                ConnectionState.IDENTIFYING,
                ConnectionState.RESUMING,
            ):
                # Calculate actual wait time with jitter to prevent thundering herds
                # https://discord.com/developers/docs/topics/gateway#sending-heartbeats
                jitter_factor = 1.0 + self._heartbeat_jitter
                wait_time = (self._heartbeat_interval / 1000) * jitter_factor

                # Wait for the next heartbeat interval
                await asyncio.sleep(wait_time)

                # Check if the last heartbeat was acknowledged
                if not self._last_heartbeat_ack:
                    logger.warning(
                        'Last heartbeat was not acknowledged, reconnecting...'
                    )
                    await self._handle_reconnect(
                        code=4000, reason='Heartbeat ACK not received'
                    )
                    return

                # Send the heartbeat
                await self._send_heartbeat()
        except asyncio.CancelledError:
            logger.debug('Heartbeat task cancelled')
        except Exception as e:
            logger.error(f'Error in heartbeat loop: {e}')
            if self.state in (
                ConnectionState.CONNECTED,
                ConnectionState.IDENTIFYING,
                ConnectionState.RESUMING,
            ):
                # Try to reconnect if we're still supposed to be connected
                await self._handle_reconnect(code=4000, reason=f'Heartbeat error: {e}')

    async def _send_heartbeat(self):
        """Send a single heartbeat packet"""
        try:
            heartbeat = {
                'op': 1,  # HEARTBEAT opcode
                'd': self._sequence,
            }
            await self._ws.send(json.dumps(heartbeat))
            logger.debug(f'Sent heartbeat with sequence {self._sequence}')
            self._last_heartbeat_ack = False  # Set to false until we get an ACK
        except Exception as e:
            logger.error(f'Failed to send heartbeat: {e}')
            raise

    async def _event_loop(self):
        """Process incoming Gateway events with improved error handling"""
        try:
            while self.state in (
                ConnectionState.CONNECTED,
                ConnectionState.IDENTIFYING,
                ConnectionState.RESUMING,
            ):
                try:
                    # Set a timeout on receive to detect stalled connections
                    message = await asyncio.wait_for(self._ws.recv(), timeout=90.0)
                    event = json.loads(message)

                    # Update sequence number if present
                    if event.get('s') is not None:
                        self._sequence = event['s']

                    # Handle different Gateway opcodes
                    if event['op'] == 0:  # DISPATCH
                        event_name = event['t']
                        event_data = event['d']

                        if event_name == 'READY':
                            self._session_id = event_data['session_id']
                            self.state = ConnectionState.CONNECTED
                            self._reconnect_attempts = (
                                0  # Reset reconnect counter on successful connection
                            )
                            logger.info(
                                f"Connected as {event_data['user']['username']}#{event_data['user']['discriminator']}"
                            )

                        elif event_name == 'RESUMED':
                            self.state = ConnectionState.CONNECTED
                            self._reconnect_attempts = (
                                0  # Reset reconnect counter on successful resume
                            )
                            logger.info('Successfully resumed session')

                        # Dispatch the event to registered callbacks
                        if event_name in self.event_callbacks:
                            try:
                                # Use create_task to prevent blocking the event loop
                                asyncio.create_task(
                                    self._dispatch_event(event_name, event_data)
                                )
                            except Exception as e:
                                logger.error(
                                    f'Error dispatching {event_name} event: {e}'
                                )

                    elif event['op'] == 7:  # RECONNECT
                        logger.info('Discord requested reconnect')
                        await self._handle_reconnect(
                            code=1000, reason='Discord requested reconnect'
                        )

                    elif event['op'] == 9:  # INVALID SESSION
                        resumable = event.get('d', False)
                        if resumable:
                            logger.warning(
                                'Invalid session but resumable, attempting to resume...'
                            )
                            await asyncio.sleep(1 + random.random())  # Add jitter
                            await self._send_resume()
                        else:
                            logger.warning(
                                'Invalid session, cannot resume, reconnecting with new session...'
                            )
                            # Clear session data
                            self._session_id = None
                            self._sequence = None
                            await asyncio.sleep(1 + random.random())  # Add jitter
                            await self._send_identify()

                    elif event['op'] == 11:  # HEARTBEAT ACK
                        logger.debug('Received heartbeat ACK')
                        self._last_heartbeat_ack = True

                except asyncio.TimeoutError:
                    logger.warning('Gateway connection timed out, reconnecting...')
                    await self._handle_reconnect(code=4000, reason='Gateway timeout')
                    break

                except (
                    websockets.exceptions.ConnectionClosed,
                    websockets.exceptions.ConnectionClosedError,
                ) as e:
                    self._close_code = e.code if hasattr(e, 'code') else 1006
                    close_reason = e.reason if hasattr(e, 'reason') else 'Unknown'

                    logger.warning(
                        f'WebSocket connection closed: Code {self._close_code}, Reason: {close_reason}'
                    )

                    if self.state != ConnectionState.DISCONNECTED:
                        # Try to reconnect unless it was an authentication failure
                        if self._close_code in (4004, 4010, 4011, 4012, 4013, 4014):
                            logger.error(
                                f'Fatal connection error {self._close_code}: {close_reason}'
                            )
                            self.state = ConnectionState.DISCONNECTED
                            break
                        else:
                            await self._handle_reconnect(
                                code=self._close_code, reason=close_reason
                            )
                    break
        except asyncio.CancelledError:
            logger.debug('Event loop task cancelled')
        except Exception as e:
            logger.error(f'Error in event loop: {e}')
            if self.state != ConnectionState.DISCONNECTED:
                # Try to reconnect
                await self._handle_reconnect(code=4000, reason=f'Event loop error: {e}')

    async def _dispatch_event(self, event_name: str, event_data: dict[str, Any]):
        """Dispatch event to callback with error handling"""
        try:
            if callback := self.event_callbacks.get(event_name):
                result = callback(event_data)
                # Handle if it's a coroutine
                if asyncio.iscoroutine(result):
                    await result
        except Exception as e:
            logger.error(f'Error in {event_name} event handler: {e}')
            import traceback

            logger.error(traceback.format_exc())

    async def _handle_reconnect(self, code=None, reason=None):
        """Handle reconnection logic with exponential backoff"""
        if self.state == ConnectionState.DISCONNECTED:
            return

        # Update state and close code
        self.state = ConnectionState.RECONNECTING
        if code:
            self._close_code = code

        # Close the websocket if it's still open
        if self._ws:
            try:
                await self._ws.close(code=1000)
            except:
                pass  # Ignore errors when closing
            self._ws = None

        # Cancel existing tasks
        if self._heartbeat_task and not self._heartbeat_task.done():
            self._heartbeat_task.cancel()

        # Schedule the reconnection with exponential backoff
        await self._schedule_reconnect()

    async def _schedule_reconnect(self):
        """Schedule a reconnection attempt with exponential backoff"""
        # Check if we should keep trying
        self._reconnect_attempts += 1
        if self._reconnect_attempts > self._max_reconnect_attempts:
            logger.error(
                f'Max reconnection attempts reached ({self._max_reconnect_attempts})'
            )
            self.state = ConnectionState.DISCONNECTED
            return

        # Calculate backoff time with exponential backoff and jitter
        backoff = min(
            self._base_backoff * (2 ** (self._reconnect_attempts - 1)),
            self._max_backoff,
        )
        jitter = random.uniform(0, 0.1 * backoff)  # Add 0-10% jitter
        wait_time = backoff + jitter

        logger.info(
            f'Reconnecting in {wait_time:.2f} seconds (attempt {self._reconnect_attempts}/{self._max_reconnect_attempts})'
        )

        # Wait the backoff time
        await asyncio.sleep(wait_time)

        # Try to reconnect
        try:
            await self._connect_and_identify()
        except Exception as e:
            logger.error(f'Reconnection failed: {e}')
            # If we're still reconnecting, schedule another attempt
            if self.state == ConnectionState.RECONNECTING:
                await self._schedule_reconnect()

    async def disconnect(self):
        """Disconnect from the Gateway"""
        logger.info('Disconnecting from Gateway')
        previous_state = self.state
        self.state = ConnectionState.DISCONNECTED

        # Cancel all tasks
        for task in (self._heartbeat_task, self._event_task, self._reconnect_task):
            if task and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        # Close the websocket connection
        if self._ws:
            try:
                # Only use 1000 (normal closure) if this was an intentional disconnect
                close_code = (
                    1000 if previous_state != ConnectionState.DISCONNECTED else 4000
                )
                await self._ws.close(code=close_code)
            except:
                pass  # Ignore errors when closing
            self._ws = None

    async def connect_sharded(self, gateway_url: str, shard_id: int, shard_count: int):
        """Connect to Discord Gateway with sharding"""
        logger.info(
            f'Connecting to Gateway with sharding: shard {shard_id}/{shard_count}'
        )

        # Store the gateway URL for reconnects
        self.gateway_url = gateway_url

        # Check if we're in mock mode
        if hasattr(sys.modules[__name__], 'REAL_API') and not REAL_API:
            logger.warning('Using mock mode for Gateway connection with sharding')
            self.state = ConnectionState.CONNECTED

            # Simulate the connection and READY event for mock mode
            async def _simulate_events():
                # Simulate a READY event
                await asyncio.sleep(0.5)
                ready_data = {
                    'v': 10,
                    'user': {
                        'id': '123456789012345678',
                        'username': 'RustCordBot',
                        'discriminator': '0000',
                        'bot': True,
                    },
                    'guilds': [
                        {
                            'id': '111222333444555666',
                            'name': f'Test Server Shard {shard_id}',
                            'owner_id': '123123123123123123',
                        }
                    ],
                    'session_id': f'abc123def456-shard-{shard_id}',
                    'shard': [shard_id, shard_count],
                }

                if 'READY' in self.event_callbacks:
                    try:
                        self.event_callbacks['READY'](ready_data)
                    except Exception as e:
                        logger.error(
                            f'Error in READY event handler for shard {shard_id}: {e}'
                        )

            # Start the event simulation in the background
            self._event_task = asyncio.create_task(_simulate_events())
            return

        # In real mode, connect to Gateway with sharding
        # Use a lock to prevent multiple connection attempts
        async with self._connection_lock:
            # Reset reconnection state
            self._reconnect_attempts = 0
            self._close_code = None

            # Store shard info for reconnects and IDENTIFY
            self.shard_id = shard_id
            self.shard_count = shard_count

            # Attempt the connection with sharding
            await self._connect_and_identify_sharded()

    async def _connect_and_identify_sharded(self):
        """Connect to the Gateway and identify with sharding information"""
        if self.state in (
            ConnectionState.CONNECTED,
            ConnectionState.IDENTIFYING,
            ConnectionState.RESUMING,
        ):
            logger.debug(f'Already in state {self.state}, not reconnecting')
            return

        try:
            self.state = ConnectionState.CONNECTING
            logger.debug(f'Connecting to Gateway with sharding: {self.gateway_url}')

            # Calculate jitter for heartbeat to prevent thundering herd
            self._heartbeat_jitter = random.uniform(-0.1, 0.1) * (
                1 + self.shard_id * 0.1
            )  # Add shard-based jitter

            # Connect to the Discord Gateway
            self._ws = await websockets.connect(
                self.gateway_url,
                ping_interval=30,
                ping_timeout=10,
                close_timeout=10,
                compression=None,
                ssl=True,
            )

            # Handle the initial hello message to get heartbeat interval
            hello_msg = await self._ws.recv()
            hello_data = json.loads(hello_msg)

            if hello_data['op'] == 10:  # HELLO
                self._heartbeat_interval = hello_data['d']['heartbeat_interval']
                self._last_heartbeat_ack = True

                # Try to resume if we have a session
                if self._session_id and self._sequence:
                    await self._send_resume()
                else:
                    await self._send_identify_sharded()

                # Start the heartbeat and event tasks as in the regular connect method
                if self._heartbeat_task and not self._heartbeat_task.done():
                    self._heartbeat_task.cancel()
                self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())

                if self._event_task and not self._event_task.done():
                    self._event_task.cancel()
                self._event_task = asyncio.create_task(self._event_loop())

                self.state = ConnectionState.IDENTIFYING
            else:
                logger.error(f'Unexpected initial message: {hello_data}')
                await self.disconnect()
                raise GatewayError('Unexpected initial Gateway message')
        except Exception as e:
            logger.error(f'Error connecting to gateway with sharding: {e}')
            self.state = ConnectionState.DISCONNECTED
            if self._ws:
                await self._ws.close()
            self._ws = None

            # Only try to reconnect if it wasn't an intentional disconnect
            if self._close_code != 1000:
                await self._schedule_reconnect()
            raise

    async def _send_identify_sharded(self):
        """Send IDENTIFY payload with sharding information to Discord Gateway"""
        logger.debug(
            f'Sending IDENTIFY payload for shard {self.shard_id}/{self.shard_count}'
        )
        self.state = ConnectionState.IDENTIFYING

        identify_payload = {
            'op': 2,  # IDENTIFY opcode
            'd': {
                'token': self.token,
                'properties': {
                    '$os': 'linux',
                    '$browser': 'rustcord',
                    '$device': 'rustcord',
                },
                'intents': self.intents,
                'shard': [self.shard_id, self.shard_count],
                'compress': False,
            },
        }

        await self._ws.send(json.dumps(identify_payload))

    async def update_voice_state(
        self,
        guild_id: str,
        channel_id: str = None,
        self_mute: bool = False,
        self_deaf: bool = False,
    ):
        """Update the bot's voice state in a guild"""
        logger.debug(
            f'Updating voice state: guild={guild_id}, channel={channel_id}, mute={self_mute}, deaf={self_deaf}'
        )

        if not self._ws or self.state != ConnectionState.CONNECTED:
            raise GatewayError('Not connected to Gateway')

        voice_state_update = {
            'op': 4,  # VOICE_STATE_UPDATE opcode
            'd': {
                'guild_id': guild_id,
                'channel_id': channel_id,  # None will disconnect
                'self_mute': self_mute,
                'self_deaf': self_deaf,
            },
        }

        await self._ws.send(json.dumps(voice_state_update))

    async def get_voice_connection(self, guild_id: str):
        """Get voice connection data for a guild if it exists"""
        # In this Python implementation we don't have a full voice implementation
        # This would be properly implemented in the Rust version
        logger.warning(
            'Voice connections are not fully implemented in the Python version'
        )

    async def create_audio_player(self):
        """Create an audio player for voice playback"""
        # In this Python implementation we don't have a full audio implementation
        # This would be properly implemented in the Rust version
        logger.warning('Audio players are not fully implemented in the Python version')
