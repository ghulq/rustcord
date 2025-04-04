"""
Discord API data models
"""

import os
from enum import IntEnum
from typing import Optional, Any, ClassVar, Type, TypeVar, Union


from . import _rust

T = TypeVar('T')


class ChannelType(IntEnum):
    """Discord Channel Types"""

    GUILD_TEXT = 0
    DM = 1
    GUILD_VOICE = 2
    GROUP_DM = 3
    GUILD_CATEGORY = 4
    GUILD_NEWS = 5
    GUILD_STORE = 6
    GUILD_NEWS_THREAD = 10
    GUILD_PUBLIC_THREAD = 11
    GUILD_PRIVATE_THREAD = 12
    GUILD_STAGE_VOICE = 13


class InteractionType(IntEnum):
    """Discord Interaction types"""

    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionResponseType(IntEnum):
    """Discord Interaction response types"""

    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9


class CommandOptionType(IntEnum):
    """Discord command option types"""

    SUB_COMMAND = 1
    SUB_COMMAND_GROUP = 2
    STRING = 3
    INTEGER = 4
    BOOLEAN = 5
    USER = 6
    CHANNEL = 7
    ROLE = 8
    MENTIONABLE = 9
    NUMBER = 10
    ATTACHMENT = 11


class PermissionType(IntEnum):
    """Discord application command permission types"""

    ROLE = 1
    USER = 2
    CHANNEL = 3


class ApplicationCommandPermission:
    """Discord application command permission"""

    __slots__ = ('id', 'type', 'permission')

    def __init__(self, id: str, type: PermissionType, permission: bool):
        """
        Initialize a new permission

        Args:
            id: ID of the role, user, or channel
            type: Type of permission target
            permission: Whether the permission is allowed (True) or denied (False)
        """
        self.id = id
        self.type = type
        self.permission = permission

    def to_dict(self) -> dict[str, Any]:
        """Convert to API payload format"""
        return {'id': self.id, 'type': int(self.type), 'permission': self.permission}


class ComponentType(IntEnum):
    """Discord UI component types"""

    ACTION_ROW = 1
    BUTTON = 2
    SELECT_MENU = 3
    TEXT_INPUT = 4
    USER_SELECT = 5
    ROLE_SELECT = 6
    MENTIONABLE_SELECT = 7
    CHANNEL_SELECT = 8


class ButtonStyle(IntEnum):
    """Discord button styles"""

    PRIMARY = 1  # Blurple
    SECONDARY = 2  # Grey
    SUCCESS = 3  # Green
    DANGER = 4  # Red
    LINK = 5  # Link (navigates to URL)


class DiscordModel:
    """Base class for Discord data models"""

    _rust_type: ClassVar[Type] = None
    __slots__ = ()

    @classmethod
    def _from_rust(cls, rust_obj):
        """Convert a Rust object to a Python model"""
        return rust_obj and cls(_rust_obj=rust_obj)


class Message(DiscordModel):
    """Discord Message model"""

    _rust_type = _rust.Message
    __slots__ = ('_rust_obj',)

    def __init__(self, *, _rust_obj=None, **kwargs):
        self._rust_obj = _rust_obj or self._rust_type(**kwargs)

    @property
    def id(self) -> str:
        """Message ID"""
        return self._rust_obj.id

    @property
    def channel_id(self) -> str:
        """Channel ID where the message was sent"""
        return self._rust_obj.channel_id

    @property
    def content(self) -> str:
        """Message content"""
        return self._rust_obj.content

    @property
    def author_id(self) -> str:
        """ID of the message author"""
        return self._rust_obj.author_id

    @property
    def author_username(self) -> str:
        """Username of the message author"""
        return self._rust_obj.author_username

    def __repr__(self) -> str:
        return f"<Message id={self.id} content='{self.content}'>"


class User(DiscordModel):
    """Discord User model"""

    _rust_type = _rust.User
    __slots__ = ('_rust_obj',)

    def __init__(self, *, _rust_obj=None, **kwargs):
        self._rust_obj = _rust_obj or self._rust_type(**kwargs)

    @property
    def id(self) -> str:
        """User ID"""
        return self._rust_obj.id

    @property
    def username(self) -> str:
        """Username"""
        return self._rust_obj.username

    @property
    def discriminator(self) -> str:
        """User discriminator"""
        return self._rust_obj.discriminator

    @property
    def bot(self) -> bool:
        """Whether this user is a bot"""
        return self._rust_obj.bot

    @property
    def tag(self) -> str:
        """User tag (username#discriminator)"""
        return f'{self.username}#{self.discriminator}'

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}'>"


class Channel(DiscordModel):
    """Discord Channel model"""

    _rust_type = _rust.Channel
    __slots__ = ('_rust_obj',)

    def __init__(self, *, _rust_obj=None, **kwargs):
        self._rust_obj = _rust_obj or self._rust_type(**kwargs)

    @property
    def id(self) -> str:
        """Channel ID"""
        return self._rust_obj.id

    @property
    def name(self) -> str:
        """Channel name"""
        return self._rust_obj.name

    @property
    def channel_type(self) -> int:
        """Channel type"""
        return self._rust_obj.channel_type

    @property
    def guild_id(self) -> Optional[str]:
        """Guild ID this channel belongs to, if any"""
        return self._rust_obj.guild_id

    def __repr__(self) -> str:
        return f"<Channel id={self.id} name='{self.name}' type={self.channel_type}>"


class Guild(DiscordModel):
    """Discord Guild model"""

    _rust_type = _rust.Guild
    __slots__ = ('_rust_obj',)

    def __init__(self, *, _rust_obj=None, **kwargs):
        self._rust_obj = _rust_obj or self._rust_type(**kwargs)

    @property
    def id(self) -> str:
        """Guild ID"""
        return self._rust_obj.id

    @property
    def name(self) -> str:
        """Guild name"""
        return self._rust_obj.name

    @property
    def owner_id(self) -> str:
        """Guild owner ID"""
        return self._rust_obj.owner_id

    def __repr__(self) -> str:
        return f"<Guild id={self.id} name='{self.name}'>"


class VoiceState(DiscordModel):
    """Discord Voice State model"""

    _rust_type = getattr(_rust, 'VoiceState', None)
    __slots__ = ('_rust_obj', '_data')

    def __init__(self, *, _rust_obj=None, **kwargs):
        if _rust_obj:
            self._rust_obj = _rust_obj
        elif self._rust_type:
            self._rust_obj = self._rust_type(**kwargs)
        else:
            # Fallback when Rust implementation is not available
            self._rust_obj = None
            self._data = kwargs

    @property
    def guild_id(self) -> Optional[str]:
        """Guild ID this voice state belongs to, if any"""
        if self._rust_obj:
            return self._rust_obj.guild_id
        return self._data.get('guild_id')

    @property
    def channel_id(self) -> Optional[str]:
        """Channel ID this voice state belongs to, if any"""
        if self._rust_obj:
            return self._rust_obj.channel_id
        return self._data.get('channel_id')

    @property
    def user_id(self) -> str:
        """User ID this voice state belongs to"""
        if self._rust_obj:
            return self._rust_obj.user_id
        return self._data.get('user_id', '')

    @property
    def session_id(self) -> str:
        """Session ID for this voice connection"""
        if self._rust_obj:
            return self._rust_obj.session_id
        return self._data.get('session_id', '')

    @property
    def deaf(self) -> bool:
        """Whether this user is deafened by the server"""
        if self._rust_obj:
            return self._rust_obj.deaf
        return self._data.get('deaf', False)

    @property
    def mute(self) -> bool:
        """Whether this user is muted by the server"""
        if self._rust_obj:
            return self._rust_obj.mute
        return self._data.get('mute', False)

    @property
    def self_deaf(self) -> bool:
        """Whether this user is locally deafened"""
        if self._rust_obj:
            return self._rust_obj.self_deaf
        return self._data.get('self_deaf', False)

    @property
    def self_mute(self) -> bool:
        """Whether this user is locally muted"""
        if self._rust_obj:
            return self._rust_obj.self_mute
        return self._data.get('self_mute', False)

    @property
    def self_stream(self) -> bool:
        """Whether this user is streaming"""
        if self._rust_obj:
            return self._rust_obj.self_stream
        return self._data.get('self_stream', False)

    @property
    def self_video(self) -> bool:
        """Whether this user has video enabled"""
        if self._rust_obj:
            return self._rust_obj.self_video
        return self._data.get('self_video', False)

    @property
    def suppress(self) -> bool:
        """Whether this user is suppressed"""
        if self._rust_obj:
            return self._rust_obj.suppress
        return self._data.get('suppress', False)

    def __repr__(self) -> str:
        return f'<VoiceState user_id={self.user_id} channel_id={self.channel_id}>'


class VoiceServerInfo(DiscordModel):
    """Discord Voice Server Information"""

    _rust_type = getattr(_rust, 'VoiceServerInfo', None)
    __slots__ = ('_rust_obj', '_data')

    def __init__(self, *, _rust_obj=None, **kwargs):
        if _rust_obj:
            self._rust_obj = _rust_obj
        elif self._rust_type:
            self._rust_obj = self._rust_type(**kwargs)
        else:
            # Fallback when Rust implementation is not available
            self._rust_obj = None
            self._data = kwargs

    @property
    def token(self) -> str:
        """Voice connection token"""
        if self._rust_obj:
            return self._rust_obj.token
        return self._data.get('token', '')

    @property
    def guild_id(self) -> str:
        """Guild ID this voice server belongs to"""
        if self._rust_obj:
            return self._rust_obj.guild_id
        return self._data.get('guild_id', '')

    @property
    def endpoint(self) -> str:
        """Voice server endpoint URL"""
        if self._rust_obj:
            return self._rust_obj.endpoint
        return self._data.get('endpoint', '')

    def __repr__(self) -> str:
        return f'<VoiceServerInfo guild_id={self.guild_id} endpoint={self.endpoint}>'


class VoiceConnection(DiscordModel):
    """Discord Voice Connection"""

    _rust_type = getattr(_rust, 'VoiceConnection', None)
    __slots__ = ('_rust_obj', '_data')

    def __init__(self, *, _rust_obj=None, **kwargs):
        if _rust_obj:
            self._rust_obj = _rust_obj
        elif self._rust_type:
            self._rust_obj = self._rust_type(**kwargs)
        else:
            # Fallback when Rust implementation is not available
            self._rust_obj = None
            self._data = kwargs

    @property
    def guild_id(self) -> str:
        """Guild ID this voice connection belongs to"""
        if self._rust_obj:
            return self._rust_obj.guild_id
        return self._data.get('guild_id', '')

    @property
    def channel_id(self) -> str:
        """Channel ID this voice connection belongs to"""
        if self._rust_obj:
            return self._rust_obj.channel_id
        return self._data.get('channel_id', '')

    @property
    def session_id(self) -> str:
        """Session ID for this voice connection"""
        if self._rust_obj:
            return self._rust_obj.session_id
        return self._data.get('session_id', '')

    @property
    def token(self) -> str:
        """Token for this voice connection"""
        if self._rust_obj:
            return self._rust_obj.token
        return self._data.get('token', '')

    @property
    def endpoint(self) -> str:
        """Endpoint for this voice connection"""
        if self._rust_obj:
            return self._rust_obj.endpoint
        return self._data.get('endpoint', '')

    @property
    def connected(self) -> bool:
        """Whether this voice connection is connected"""
        if self._rust_obj:
            return self._rust_obj.connected
        return self._data.get('connected', False)

    @property
    def self_mute(self) -> bool:
        """Whether this voice connection is muted"""
        if self._rust_obj:
            return self._rust_obj.self_mute
        return self._data.get('self_mute', False)

    @property
    def self_deaf(self) -> bool:
        """Whether this voice connection is deafened"""
        if self._rust_obj:
            return self._rust_obj.self_deaf
        return self._data.get('self_deaf', False)

    async def connect(self) -> None:
        """Connect to the voice channel"""
        if self._rust_obj:
            self._rust_obj.connect()
        else:
            # Fallback: Just update the connected state
            self._data['connected'] = True

    async def disconnect(self) -> None:
        """Disconnect from the voice channel"""
        if self._rust_obj:
            self._rust_obj.disconnect()
        else:
            # Fallback: Just update the connected state
            self._data['connected'] = False

    async def set_self_mute(self, mute: bool) -> None:
        """Set whether this connection is muted"""
        if self._rust_obj:
            self._rust_obj.set_self_mute(mute)
        else:
            # Fallback: Just update the state
            self._data['self_mute'] = mute

    async def set_self_deaf(self, deaf: bool) -> None:
        """Set whether this connection is deafened"""
        if self._rust_obj:
            self._rust_obj.set_self_deaf(deaf)
        else:
            # Fallback: Just update the state
            self._data['self_deaf'] = deaf

    def __repr__(self) -> str:
        return f'<VoiceConnection guild_id={self.guild_id} channel_id={self.channel_id} connected={self.connected}>'


class AudioPlayer(DiscordModel):
    """Discord Audio Player"""

    _rust_type = getattr(_rust, 'AudioPlayer', None)
    __slots__ = ('_rust_obj', '_data')

    def __init__(self, *, _rust_obj=None, **kwargs):
        if _rust_obj:
            self._rust_obj = _rust_obj
        elif self._rust_type:
            self._rust_obj = self._rust_type(**kwargs)
        else:
            # Fallback when Rust implementation is not available
            self._rust_obj = None
            self._data = kwargs.copy()
            self._data.setdefault('is_playing', False)
            self._data.setdefault('is_paused', False)
            self._data.setdefault('volume', 1.0)

    @property
    def is_playing(self) -> bool:
        """Whether this player is currently playing audio"""
        if self._rust_obj:
            return self._rust_obj.is_playing
        return self._data.get('is_playing', False)

    @property
    def is_paused(self) -> bool:
        """Whether this player is currently paused"""
        if self._rust_obj:
            return self._rust_obj.is_paused
        return self._data.get('is_paused', False)

    @property
    def volume(self) -> float:
        """The current volume for this player (0.0 to 2.0)"""
        if self._rust_obj:
            return self._rust_obj.volume
        return self._data.get('volume', 1.0)

    async def attach(self, connection: VoiceConnection) -> None:
        """Attach this player to a voice connection"""
        if self._rust_obj and connection._rust_obj:
            self._rust_obj.attach(connection._rust_obj)
        else:
            # Fallback: Just store the connection reference
            self._data['connection'] = connection

    async def play_file(self, file_path: str) -> bool:
        """
        Play audio from a file

        Args:
            file_path: Path to the audio file to play

        Returns:
            True if playback started, False otherwise
        """
        if self._rust_obj:
            return self._rust_obj.play_file(file_path)

        # Fallback: Just update state
        self._data['is_playing'] = True
        self._data['is_paused'] = False
        self._data['current_file'] = file_path
        return False  # Indicate that actual playback didn't start

    async def stop(self) -> None:
        """Stop playback"""
        if self._rust_obj:
            self._rust_obj.stop()
        else:
            # Fallback: Just update state
            self._data['is_playing'] = False
            self._data['is_paused'] = False

    async def pause(self) -> None:
        """Pause playback"""
        if self._rust_obj:
            self._rust_obj.pause()
        else:
            # Fallback: Just update state
            self._data['is_paused'] = True

    async def resume(self) -> None:
        """Resume playback"""
        if self._rust_obj:
            self._rust_obj.resume()
        else:
            # Fallback: Just update state
            self._data['is_paused'] = False

    async def set_volume(self, volume: float) -> None:
        """
        Set the volume for this player

        Args:
            volume: The volume to set (0.0 to 2.0)
        """
        if self._rust_obj:
            self._rust_obj.set_volume(volume)
        else:
            # Fallback: Just update state
            self._data['volume'] = max(0.0, min(volume, 2.0))

    def __repr__(self) -> str:
        return f'<AudioPlayer playing={self.is_playing} paused={self.is_paused} volume={self.volume}>'


class CommandOption:
    """Discord Application Command Option"""

    __slots__ = (
        'type',
        'name',
        'description',
        'required',
        'choices',
        'options',
        'autocomplete',
        'min_value',
        'max_value',
        'channel_types',
    )

    def __init__(
        self,
        type: CommandOptionType,
        name: str,
        description: str,
        required: bool = False,
        choices: Optional[list[dict[str, Union[str, int, float]]]] = None,
        options: Optional[list['CommandOption']] = None,
        autocomplete: bool = False,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        channel_types: Optional[list[ChannelType]] = None,
    ):
        """
        Initialize a new command option

        Args:
            type: Type of the option
            name: Name of the option (1-32 characters)
            description: Description of the option (1-100 characters)
            required: Whether this option is required
            choices: Predefined choices for the user
            options: Sub-options for this option (for subcommands)
            autocomplete: Whether this option should use autocomplete
            min_value: Minimum value for INTEGER and NUMBER options
            max_value: Maximum value for INTEGER and NUMBER options
            channel_types: Channel types to include for CHANNEL options
        """
        self.type = type
        self.name = name
        self.description = description
        self.required = required
        self.choices = choices or []
        self.options = options or []
        self.autocomplete = autocomplete
        self.min_value = min_value
        self.max_value = max_value
        self.channel_types = channel_types or []

    def to_dict(self) -> dict[str, Any]:
        """Convert to API payload format"""
        data = {
            'type': int(self.type),
            'name': self.name,
            'description': self.description,
            'required': self.required,
        }

        # Add autocomplete if enabled (only for STRING, INTEGER, or NUMBER types)
        if self.autocomplete and self.type in (
            CommandOptionType.STRING,
            CommandOptionType.INTEGER,
            CommandOptionType.NUMBER,
        ):
            data['autocomplete'] = True

        # Choices and autocomplete are mutually exclusive
        if self.choices and not self.autocomplete:
            data['choices'] = self.choices

        # Add min/max values for numeric types
        if self.min_value is not None and self.type in (
            CommandOptionType.INTEGER,
            CommandOptionType.NUMBER,
        ):
            data['min_value'] = self.min_value

        if self.max_value is not None and self.type in (
            CommandOptionType.INTEGER,
            CommandOptionType.NUMBER,
        ):
            data['max_value'] = self.max_value

        # Add channel types for CHANNEL type options
        if self.channel_types and self.type == CommandOptionType.CHANNEL:
            data['channel_types'] = [int(t) for t in self.channel_types]

        if self.options:
            data['options'] = [opt.to_dict() for opt in self.options]

        return data


class ApplicationCommand:
    """Discord Application Command (Slash Command)"""

    __slots__ = (
        'name',
        'description',
        'options',
        'default_permission',
        'default_member_permissions',
        'dm_permission',
        'guild_id',
        'permissions',
        'id',
    )

    def __init__(
        self,
        name: str,
        description: str,
        options: Optional[list[CommandOption]] = None,
        default_permission: bool = True,
        default_member_permissions: Optional[str] = None,
        dm_permission: bool = True,
        guild_id: Optional[str] = None,
        permissions: Optional[list[ApplicationCommandPermission]] = None,
    ):
        """
        Initialize a new application command

        Args:
            name: Name of command (3-32 characters)
            description: Description (1-100 characters)
            options: Command options
            default_permission: (Deprecated) Whether the command is enabled by default
            default_member_permissions: String representing the permissions as an integer bitfield
            dm_permission: Whether the command is available in DMs
            guild_id: Guild ID if this is a guild command
            permissions: Command-specific permissions
        """
        self.name = name
        self.description = description
        self.options = options or []
        self.default_permission = default_permission
        self.default_member_permissions = default_member_permissions
        self.dm_permission = dm_permission
        self.guild_id = guild_id
        self.permissions = permissions or []
        self.id = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to API payload format"""
        data = {
            'name': self.name,
            'description': self.description,
        }

        # For backwards compatibility, still include default_permission
        data['default_permission'] = self.default_permission

        # New permission system
        if self.default_member_permissions is not None:
            data['default_member_permissions'] = self.default_member_permissions

        # DM permissions, only include if False as True is the default
        if not self.dm_permission:
            data['dm_permission'] = False

        if self.options:
            data['options'] = [opt.to_dict() for opt in self.options]

        return data

    def get_permissions_payload(self) -> dict[str, Any]:
        """Get the permissions payload for this command"""
        if not self.id:
            raise ValueError('Command must be registered before setting permissions')

        if not self.guild_id:
            raise ValueError('Permissions can only be set for guild commands')

        return {
            'id': self.id,
            'application_id': None,  # Will be filled in by the client
            'guild_id': self.guild_id,
            'permissions': [perm.to_dict() for perm in self.permissions],
        }


class Component:
    """Base class for all Discord UI components"""

    __slots__ = ()

    def to_dict(self) -> dict[str, Any]:
        """Convert to component API payload format"""
        raise NotImplementedError('Subclasses must implement to_dict()')


class Button(Component):
    """Discord UI Button component"""

    __slots__ = ('style', 'label', 'custom_id', 'url', 'emoji', 'disabled')

    def __init__(
        self,
        style: ButtonStyle = ButtonStyle.PRIMARY,
        label: Optional[str] = None,
        custom_id: Optional[str] = None,
        url: Optional[str] = None,
        emoji: Optional[Union[str, dict[str, Any]]] = None,
        disabled: bool = False,
    ):
        """
        Initialize a new button component

        Args:
            style: Button style
            label: Button label text
            custom_id: ID to identify this button when clicked (required for non-link buttons)
            url: URL for link buttons (required for link buttons)
            emoji: Emoji to display on the button (can be unicode emoji or custom emoji dict)
            disabled: Whether the button is disabled
        """
        self.style = style
        self.label = label
        self.custom_id = custom_id
        self.url = url
        self.emoji = emoji
        self.disabled = disabled

        # Validate based on button style
        if style == ButtonStyle.LINK:
            if url is None:
                raise ValueError('URL must be provided for LINK buttons')
            if custom_id is not None:
                raise ValueError('custom_id cannot be used with LINK buttons')
        else:
            if custom_id is None:
                raise ValueError('custom_id must be provided for non-LINK buttons')
            if url is not None:
                raise ValueError('url cannot be used with non-LINK buttons')

    def to_dict(self) -> dict[str, Any]:
        """Convert to component API payload format"""
        data = {
            'type': ComponentType.BUTTON,
            'style': self.style,
            'disabled': self.disabled,
        }

        if self.label:
            data['label'] = self.label

        if self.style == ButtonStyle.LINK:
            data['url'] = self.url
        else:
            data['custom_id'] = self.custom_id

        if self.emoji:
            if isinstance(self.emoji, str):
                data['emoji'] = {'name': self.emoji}
            else:
                data['emoji'] = self.emoji

        return data


class SelectOption:
    """Option for Discord select menu components"""

    __slots__ = ('label', 'value', 'description', 'emoji', 'default')

    def __init__(
        self,
        label: str,
        value: str,
        description: Optional[str] = None,
        emoji: Optional[Union[str, dict[str, Any]]] = None,
        default: bool = False,
    ):
        """
        Initialize a new select option

        Args:
            label: User-facing name of the option (max 100 chars)
            value: Dev-defined value of the option (max 100 chars)
            description: Additional description (max 100 chars)
            emoji: Emoji displayed on this option
            default: Whether this option is selected by default
        """
        self.label = label
        self.value = value
        self.description = description
        self.emoji = emoji
        self.default = default

    def to_dict(self) -> dict[str, Any]:
        """Convert to API payload format"""
        data = {'label': self.label, 'value': self.value, 'default': self.default}

        if self.description:
            data['description'] = self.description

        if self.emoji:
            if isinstance(self.emoji, str):
                data['emoji'] = {'name': self.emoji}
            else:
                data['emoji'] = self.emoji

        return data


class SelectMenu(Component):
    """Discord select menu component"""

    __slots__ = (
        'custom_id',
        'options',
        'placeholder',
        'min_values',
        'max_values',
        'disabled',
        'type',
    )

    def __init__(
        self,
        custom_id: str,
        options: Optional[list[SelectOption]] = None,
        placeholder: Optional[str] = None,
        min_values: int = 1,
        max_values: int = 1,
        disabled: bool = False,
        type: ComponentType = ComponentType.SELECT_MENU,
    ):
        """
        Initialize a new select menu component

        Args:
            custom_id: ID to identify this menu when used (max 100 chars)
            options: Available choices in the menu (max 25)
            placeholder: Placeholder text when no option is selected
            min_values: Minimum number of options that must be chosen (0-25)
            max_values: Maximum number of options that can be chosen (1-25)
            disabled: Whether this menu is disabled
            type: Type of select menu (default: generic select)
        """
        self.custom_id = custom_id
        self.options = options or []
        self.placeholder = placeholder
        self.min_values = min_values
        self.max_values = max_values
        self.disabled = disabled
        self.type = type

        # Validate
        if len(self.options) > 25:
            raise ValueError('Select menus can have at most 25 options')
        if self.min_values < 0 or self.min_values > 25:
            raise ValueError('min_values must be between 0 and 25')
        if self.max_values < 1 or self.max_values > 25:
            raise ValueError('max_values must be between 1 and 25')
        if self.min_values > self.max_values:
            raise ValueError('min_values cannot be greater than max_values')

    def to_dict(self) -> dict[str, Any]:
        """Convert to component API payload format"""
        data = {
            'type': self.type,
            'custom_id': self.custom_id,
            'min_values': self.min_values,
            'max_values': self.max_values,
            'disabled': self.disabled,
        }

        # Only include options for regular select menus
        if self.type == ComponentType.SELECT_MENU:
            data['options'] = [option.to_dict() for option in self.options]

        if self.placeholder:
            data['placeholder'] = self.placeholder

        return data


class ActionRow(Component):
    """Discord Action Row component container"""

    __slots__ = ('components',)

    def __init__(self, components: Optional[list[Component]] = None):
        """
        Initialize a new action row

        Args:
            components: List of components in this row (max 5)
        """
        self.components = components or []

        # Validate
        if len(self.components) > 5:
            raise ValueError('Action rows can have at most 5 components')

    def to_dict(self) -> dict[str, Any]:
        """Convert to component API payload format"""
        return {
            'type': ComponentType.ACTION_ROW,
            'components': [component.to_dict() for component in self.components],
        }


class Interaction:
    """Discord Interaction model for slash commands and components"""

    __slots__ = (
        'id',
        'application_id',
        'type',
        'data',
        'guild_id',
        'channel_id',
        'member',
        'user',
        'token',
        'version',
        'message',
        'command_name',
        'command_id',
        'options',
        'component_type',
        'custom_id',
        'values',
        'focused_option',
    )

    def __init__(self, data: dict[str, Any]):
        """
        Initialize from raw interaction data

        Args:
            data: Raw API data for the interaction
        """
        self.id = data.get('id')
        self.application_id = data.get('application_id')
        self.type = InteractionType(data.get('type'))
        self.data = data.get('data', {})
        self.guild_id = data.get('guild_id')
        self.channel_id = data.get('channel_id')
        self.member = data.get('member', {})
        self.user = data.get('user', {})
        self.token = data.get('token', '')
        self.version = data.get('version', 1)
        self.message = data.get('message', {})

        # Command details if this is an application command
        if self.type == InteractionType.APPLICATION_COMMAND:
            self.command_name = self.data.get('name', '')
            self.command_id = self.data.get('id')
            self.options = self.data.get('options', [])
        # Component details if this is a component interaction
        elif self.type == InteractionType.MESSAGE_COMPONENT:
            self.component_type = self.data.get('component_type', 0)
            self.custom_id = self.data.get('custom_id', '')
            self.values = self.data.get('values', [])  # For select menus
            self.command_name = ''
            self.command_id = None
            self.options = []
        # Autocomplete details if this is an autocomplete interaction
        elif self.type == InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
            self.command_name = self.data.get('name', '')
            self.command_id = self.data.get('id')
            self.options = self.data.get('options', [])
            # The option that is currently being typed by the user
            self.focused_option = None
            # Find the option that has focus=True
            for option in self.options:
                if option.get('focused', False):
                    self.focused_option = option
                    break
        else:
            self.command_name = ''
            self.command_id = None
            self.options = []
            self.custom_id = ''
            self.values = []
            self.focused_option = None

    def get_option(self, name: str) -> Optional[dict[str, Any]]:
        """
        Get an option from the interaction by name

        Args:
            name: Option name to look for

        Returns:
            Option data if found, None otherwise
        """
        for option in self.options:
            if option.get('name') == name:
                return option

    def get_option_value(self, name: str, default: Any = None) -> Any:
        """
        Get the value of an option by name

        Args:
            name: Option name to look for
            default: Default value if not found

        Returns:
            Option value if found, default otherwise
        """
        if option := self.get_option(name):
            return option.get('value', default)
        return default

    @property
    def user_id(self) -> Optional[str]:
        """Get the ID of the user who triggered this interaction"""
        if self.member and 'user' in self.member:
            return self.member.get('user', {}).get('id')
        if self.user:
            return self.user.get('id')

    @property
    def username(self) -> Optional[str]:
        """Get the username of the user who triggered this interaction"""
        if self.member and 'user' in self.member:
            return self.member.get('user', {}).get('username')
        if self.user:
            return self.user.get('username')

    async def respond(
        self,
        content: Optional[str] = None,
        ephemeral: bool = False,
        embeds: Optional[list[dict[str, Any]]] = None,
        components: Optional[list[Component]] = None,
    ) -> None:
        """
        Respond to this interaction

        Args:
            content: Text content for the response
            ephemeral: Whether the response should be ephemeral (only visible to the command invoker)
            embeds: List of embeds for the response
            components: List of UI components to include in the response
        """
        # Import here to avoid circular imports
        from . import _rust

        # Verify we have a valid interaction ID and token
        if not self.id or not self.token:
            raise ValueError('Cannot respond to interaction without valid ID and token')

        # Create response data
        data = {
            'type': InteractionResponseType.CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'flags': 64 if ephemeral else 0},
        }

        if content:
            data['data']['content'] = content

        if embeds:
            data['data']['embeds'] = embeds

        # Convert any components to action rows if needed
        if components:
            action_rows = []

            for component in components:
                # If the component is already an action row, add it directly
                if isinstance(component, ActionRow):
                    action_rows.append(component.to_dict())
                # Otherwise, wrap it in an action row first
                else:
                    action_row = ActionRow(components=[component])
                    action_rows.append(action_row.to_dict())

            if action_rows:
                data['data']['components'] = action_rows

        # Get a client instance to respond
        client = _rust.DiscordClient(os.environ.get('DISCORD_TOKEN', ''))
        await client.create_interaction_response(self.id, self.token, data)

    async def defer_response(self, ephemeral: bool = False) -> None:
        """
        Defer the response to this interaction

        Args:
            ephemeral: Whether the deferred response should be ephemeral
        """
        # Import here to avoid circular imports
        from . import _rust

        # Verify we have a valid interaction ID and token
        if not self.id or not self.token:
            raise ValueError(
                'Cannot defer interaction response without valid ID and token'
            )

        # Create deferred response data
        data = {
            'type': InteractionResponseType.DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE,
            'data': {'flags': 64 if ephemeral else 0},
        }

        # Get a client instance to respond
        client = _rust.DiscordClient(os.environ.get('DISCORD_TOKEN', ''))
        await client.create_interaction_response(self.id, self.token, data)

    async def respond_autocomplete(self, choices: list[dict[str, Any]]) -> None:
        """
        Respond to an autocomplete interaction with choices

        Args:
            choices: List of choice objects with name and value properties
                Example: [{'name': 'Choice 1', 'value': 'value1'}, ...]
        """
        # Import here to avoid circular imports
        from . import _rust

        # Make sure this is an autocomplete interaction
        if self.type != InteractionType.APPLICATION_COMMAND_AUTOCOMPLETE:
            raise ValueError('This is not an autocomplete interaction')

        # Verify we have a valid interaction ID and token
        if not self.id or not self.token:
            raise ValueError(
                'Cannot respond to autocomplete without valid ID and token'
            )

        # Maximum 25 choices
        if len(choices) > 25:
            choices = choices[:25]

        # Create autocomplete response data
        data = {
            'type': InteractionResponseType.APPLICATION_COMMAND_AUTOCOMPLETE_RESULT,
            'data': {'choices': choices},
        }

        # Get a client instance to respond
        client = _rust.DiscordClient(os.environ.get('DISCORD_TOKEN', ''))
        await client.create_interaction_response(self.id, self.token, data)
