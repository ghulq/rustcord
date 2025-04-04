"""
Discord Gateway (WebSocket) connection handling
"""

import asyncio
import logging
from enum import Enum
from typing import Any, Union
from collections.abc import Awaitable, Callable

from . import _rust

logger = logging.getLogger(__name__)


class GatewayEvent(Enum):
    """Discord Gateway event types"""

    READY = 'READY'
    MESSAGE_CREATE = 'MESSAGE_CREATE'
    MESSAGE_UPDATE = 'MESSAGE_UPDATE'
    MESSAGE_DELETE = 'MESSAGE_DELETE'
    CHANNEL_CREATE = 'CHANNEL_CREATE'
    CHANNEL_UPDATE = 'CHANNEL_UPDATE'
    CHANNEL_DELETE = 'CHANNEL_DELETE'
    GUILD_CREATE = 'GUILD_CREATE'
    GUILD_UPDATE = 'GUILD_UPDATE'
    GUILD_DELETE = 'GUILD_DELETE'
    GUILD_MEMBER_ADD = 'GUILD_MEMBER_ADD'
    GUILD_MEMBER_UPDATE = 'GUILD_MEMBER_UPDATE'
    GUILD_MEMBER_REMOVE = 'GUILD_MEMBER_REMOVE'
    TYPING_START = 'TYPING_START'
    PRESENCE_UPDATE = 'PRESENCE_UPDATE'
    VOICE_STATE_UPDATE = 'VOICE_STATE_UPDATE'
    INTERACTION_CREATE = 'INTERACTION_CREATE'  # For slash commands and interactions


# Type definition for event handlers
EventHandler = Callable[[dict[str, Any]], Union[None, Awaitable[None]]]


class Gateway:
    """
    Low-level interface to Discord Gateway

    This is a Python wrapper around the Rust GatewayClient
    """

    __slots__ = ('token', 'intents', '_gateway', '_event_handlers')

    def __init__(self, token: str, intents: int):
        """
        Initialize Gateway connection manager

        Args:
            token: Discord bot token
            intents: Gateway intents flags
        """
        self.token = token
        self.intents = intents
        self._gateway = _rust.GatewayClient(token, intents)
        self._event_handlers: dict[str, list[EventHandler]] = {}

    async def connect(self, gateway_url: str):
        """
        Connect to Discord Gateway

        Args:
            gateway_url: WebSocket URL for Gateway connection
        """
        logger.debug(f'Connecting to Gateway at {gateway_url}')

        # Register handlers for each event type
        for event in self._event_handlers.keys():

            def create_handler(event_name):
                async def handler(data):
                    await self._dispatch_event(event_name, data)

                return handler

            self._gateway.on(event, create_handler(event))

        await self._gateway.connect(gateway_url)

    async def disconnect(self):
        """Disconnect from Discord Gateway"""
        await self._gateway.disconnect()

    async def _dispatch_event(self, event_name: str, data: dict[str, Any]):
        """Dispatch an event to all registered handlers"""
        handlers = self._event_handlers.get(event_name, [])
        for handler in handlers:
            try:
                result = handler(data)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception(f'Error in event handler for {event_name}: {e}')

    def on(self, event: Union[str, GatewayEvent], handler: EventHandler):
        """
        Register a handler for a Gateway event

        Args:
            event: Event type to listen for
            handler: Function to call when event is received
        """
        if isinstance(event, GatewayEvent):
            event = event.value

        if event not in self._event_handlers:
            self._event_handlers[event] = []

        self._event_handlers[event].append(handler)

        return handler  # Allow use as decorator
