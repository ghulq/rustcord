"""
RustCord: High-performance Discord API library with Rust core
"""

import logging

from . import _rust
from .client import Client, Intents
from .models import (
    Message,
    User,
    Channel,
    Guild,
    ChannelType,
    VoiceState,
    VoiceServerInfo,
    VoiceConnection,
    AudioPlayer,
    Interaction,
    ApplicationCommand,
    CommandOption,
    CommandOptionType,
    InteractionType,
    InteractionResponseType,
    Component,
    Button,
    ButtonStyle,
    SelectMenu,
    SelectOption,
    ActionRow,
    ComponentType,
)
from .errors import DiscordError, GatewayError, HTTPError
from .gateway import GatewayEvent
from .embeds import Embed, Color, create_embed

__version__ = _rust.__version__

# Configure logging
logging.basicConfig(
    level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('rustcord')

# Export important classes and functions
__all__ = [
    'Client',
    'Intents',
    'Message',
    'User',
    'Channel',
    'Guild',
    'ChannelType',
    'VoiceState',
    'VoiceServerInfo',
    'VoiceConnection',
    'AudioPlayer',
    'Interaction',
    'ApplicationCommand',
    'CommandOption',
    'CommandOptionType',
    'InteractionType',
    'InteractionResponseType',
    'Component',
    'Button',
    'ButtonStyle',
    'SelectMenu',
    'SelectOption',
    'ActionRow',
    'ComponentType',
    'GatewayEvent',
    'DiscordError',
    'GatewayError',
    'HTTPError',
    'Embed',
    'Color',
    'create_embed',
]
