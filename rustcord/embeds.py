"""
Discord Rich Embed builder module for RustCord

This module provides a clean API for building rich embeds for Discord messages.
"""

from datetime import datetime
from typing import Any, Optional, Union


class Color:
    """Discord embed colors"""

    DEFAULT = 0x000000
    WHITE = 0xFFFFFF
    AQUA = 0x1ABC9C
    GREEN = 0x2ECC71
    BLUE = 0x3498DB
    PURPLE = 0x9B59B6
    LUMINOUS_VIVID_PINK = 0xE91E63
    GOLD = 0xF1C40F
    ORANGE = 0xE67E22
    RED = 0xE74C3C
    GREY = 0x95A5A6
    NAVY = 0x34495E
    DARK_AQUA = 0x11806A
    DARK_GREEN = 0x1F8B4C
    DARK_BLUE = 0x206694
    DARK_PURPLE = 0x71368A
    DARK_VIVID_PINK = 0xAD1457
    DARK_GOLD = 0xC27C0E
    DARK_ORANGE = 0xA84300
    DARK_RED = 0x992D22
    DARK_GREY = 0x979C9F
    DARKER_GREY = 0x7F8C8D
    LIGHT_GREY = 0xBCC0C0
    DARK_NAVY = 0x2C3E50
    BLURPLE = 0x5865F2
    GREYPLE = 0x99AAB5
    DARK_BUT_NOT_BLACK = 0x2C2F33
    NOT_QUITE_BLACK = 0x23272A

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> int:
        """Convert RGB values to Discord color integer

        Args:
            r: Red component (0-255)
            g: Green component (0-255)
            b: Blue component (0-255)

        Returns:
            Discord color integer
        """
        return (r << 16) + (g << 8) + b


class EmbedField:
    """Represents a field in a Discord embed."""

    __slots__ = ('name', 'value', 'inline')

    def __init__(self, name: str, value: str, inline: bool = False):
        """Initialize an embed field

        Args:
            name: Name of the field (max 256 characters)
            value: Value of the field (max 1024 characters)
            inline: Whether the field should be displayed inline
        """
        self.name = name[:256] if name else ''
        self.value = value[:1024] if value else ''
        self.inline = inline

    def to_dict(self) -> dict[str, Any]:
        """Convert field to API payload format"""
        return {'name': self.name, 'value': self.value, 'inline': self.inline}


class Embed:
    """Discord Rich Embed builder

    This class provides a clean API for building rich embeds for Discord messages.

    Example:
        ```python
        embed = Embed(title='Hello, world!', description='This is a description')
        embed.set_color(Color.BLUE)
        embed.add_field('Field 1', 'Value 1', inline=True)
        embed.add_field('Field 2', 'Value 2', inline=True)
        embed.set_thumbnail('https://example.com/thumbnail.png')
        embed.set_image('https://example.com/image.png')
        embed.set_footer('Footer text', 'https://example.com/footer_icon.png')

        # Convert to API payload format
        embed_dict = embed.to_dict()
        ```
    """

    __slots__ = (
        'title',
        'description',
        'color',
        'url',
        'timestamp',
        '_fields',
        '_author',
        '_footer',
        '_image',
        '_thumbnail',
    )

    def __init__(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
        color: Optional[int] = None,
        url: Optional[str] = None,
        timestamp: Optional[Union[datetime, str]] = None,
    ):
        """Initialize a new Discord embed

        Args:
            title: Title of the embed (max 256 characters)
            description: Description of the embed (max 4096 characters)
            color: Color of the embed sidebar
            url: URL for the title to link to
            timestamp: Timestamp to display at bottom of embed
        """
        self.title = title[:256] if title else None
        self.description = description[:4096] if description else None
        self.color = color
        self.url = url
        self.timestamp = timestamp
        self._fields: list[EmbedField] = []
        self._author: Optional[dict[str, Any]] = None
        self._footer: Optional[dict[str, Any]] = None
        self._image: Optional[dict[str, Any]] = None
        self._thumbnail: Optional[dict[str, Any]] = None

    def set_title(self, title: str) -> 'Embed':
        """Set the title of the embed

        Args:
            title: Title text (max 256 characters)

        Returns:
            Self for method chaining
        """
        self.title = title[:256] if title else None
        return self

    def set_description(self, description: str) -> 'Embed':
        """Set the description of the embed

        Args:
            description: Description text (max 4096 characters)

        Returns:
            Self for method chaining
        """
        self.description = description[:4096] if description else None
        return self

    def set_color(self, color: int) -> 'Embed':
        """Set the color of the embed sidebar

        Args:
            color: Color integer value (e.g. 0x3498DB for blue)

        Returns:
            Self for method chaining
        """
        self.color = color
        return self

    def set_url(self, url: str) -> 'Embed':
        """Set the URL for the title to link to

        Args:
            url: URL string

        Returns:
            Self for method chaining
        """
        self.url = url
        return self

    def set_timestamp(self, timestamp: Union[datetime, str]) -> 'Embed':
        """Set the timestamp to display at the bottom of the embed

        Args:
            timestamp: Either a datetime object or an ISO-8601 formatted string

        Returns:
            Self for method chaining
        """
        self.timestamp = timestamp
        return self

    def set_author(
        self, name: str, url: Optional[str] = None, icon_url: Optional[str] = None
    ) -> 'Embed':
        """Set the author information for the embed

        Args:
            name: Name of the author (max 256 characters)
            url: URL to link the author name to
            icon_url: URL for the author icon

        Returns:
            Self for method chaining
        """
        self._author = {'name': name[:256]}

        if url:
            self._author['url'] = url

        if icon_url:
            self._author['icon_url'] = icon_url

        return self

    def set_thumbnail(self, url: str) -> 'Embed':
        """Set the thumbnail image for the embed

        Args:
            url: Image URL

        Returns:
            Self for method chaining
        """
        self._thumbnail = {'url': url}
        return self

    def set_image(self, url: str) -> 'Embed':
        """Set the main image for the embed

        Args:
            url: Image URL

        Returns:
            Self for method chaining
        """
        self._image = {'url': url}
        return self

    def set_footer(self, text: str, icon_url: Optional[str] = None) -> 'Embed':
        """Set the footer for the embed

        Args:
            text: Footer text (max 2048 characters)
            icon_url: URL for the footer icon

        Returns:
            Self for method chaining
        """
        self._footer = {'text': text[:2048]}

        if icon_url:
            self._footer['icon_url'] = icon_url

        return self

    def add_field(self, name: str, value: str, inline: bool = False) -> 'Embed':
        """Add a field to the embed

        Args:
            name: Field name (max 256 characters)
            value: Field value (max 1024 characters)
            inline: Whether the field should be displayed inline

        Returns:
            Self for method chaining
        """
        if len(self._fields) < 25:  # Discord has a limit of 25 fields
            self._fields.append(EmbedField(name, value, inline))
        return self

    def clear_fields(self) -> 'Embed':
        """Clear all fields from the embed

        Returns:
            Self for method chaining
        """
        self._fields = []
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert the embed to API payload format

        Returns:
            API-ready embed data
        """
        embed_dict: dict[str, Any] = {}

        if self.title:
            embed_dict['title'] = self.title

        if self.description:
            embed_dict['description'] = self.description

        if self.color:
            embed_dict['color'] = self.color

        if self.url:
            embed_dict['url'] = self.url

        if self.timestamp:
            if isinstance(self.timestamp, datetime):
                embed_dict['timestamp'] = self.timestamp.isoformat()
            else:
                embed_dict['timestamp'] = self.timestamp

        if self._author:
            embed_dict['author'] = self._author

        if self._thumbnail:
            embed_dict['thumbnail'] = self._thumbnail

        if self._image:
            embed_dict['image'] = self._image

        if self._footer:
            embed_dict['footer'] = self._footer

        if self._fields:
            embed_dict['fields'] = [field.to_dict() for field in self._fields]

        return embed_dict


def create_embed(
    title: Optional[str] = None,
    description: Optional[str] = None,
    color: Optional[int] = None,
    **kwargs,
) -> Embed:
    """Helper function to quickly create an embed

    Args:
        title: Embed title
        description: Embed description
        color: Embed color
        **kwargs: Additional embed parameters

    Returns:
        New Embed object
    """
    embed = Embed(title=title, description=description, color=color)

    # Apply additional attributes if provided
    if url := kwargs.get('url'):
        embed.set_url(url)

    if timestamp := kwargs.get('timestamp'):
        embed.set_timestamp(timestamp)

    # Author
    if author_name := kwargs.get('author_name'):
        author_url = kwargs.get('author_url')
        author_icon = kwargs.get('author_icon_url')
        embed.set_author(author_name, author_url, author_icon)

    # Footer
    if footer_text := kwargs.get('footer_text'):
        footer_icon = kwargs.get('footer_icon_url')
        embed.set_footer(footer_text, footer_icon)

    # Images
    if thumbnail_url := kwargs.get('thumbnail_url'):
        embed.set_thumbnail(thumbnail_url)

    if image_url := kwargs.get('image_url'):
        embed.set_image(image_url)

    # Fields
    fields = kwargs.get('fields')
    if fields and isinstance(fields, list):
        for field in fields:
            if isinstance(field, dict) and 'name' in field and 'value' in field:
                inline = field.get('inline', False)
                embed.add_field(field['name'], field['value'], inline)

    return embed
