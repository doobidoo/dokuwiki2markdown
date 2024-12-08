"""Media and link conversion for DokuWiki to Markdown."""

import re
from pathlib import Path
from typing import Optional

class MediaConverter:
    """Converts DokuWiki media and links to Markdown format."""
    
    def __init__(self, default_image_width: int = 300):
        self.default_image_width = default_image_width
        self.image_extensions = {'jpg', 'jpeg', 'png', 'svg', 'gif'}

    def convert(self, content: str, root_path: Path) -> str:
        """Convert DokuWiki media and links to Markdown format."""
        # Convert media/image links
        content = re.sub(
            r'\{\{([^|}]+)(?:\|(?:[^}]+))?\}\}',
            self._convert_media_link,
            content
        )
        
        # Convert internal links
        content = re.sub(
            r'\[\[([^|]+)(?:\|([^]]+))?\]\]',
            lambda m: self._convert_link(m, root_path),
            content
        )
        
        return content

    def _convert_media_link(self, match) -> str:
        """Convert a DokuWiki media link to Markdown format."""
        path = match.group(1)
        caption = match.group(2) if len(match.groups()) > 1 else None
        
        # Clean up the path
        clean_path = path.split(':')[-1]  # Get last part of path
        clean_path = clean_path.split('?')[0]  # Remove query parameters
        
        extension = clean_path.split('.')[-1].lower() if '.' in clean_path else ''
        is_image = extension in self.image_extensions
        
        if is_image:
            return f"![[{clean_path} | {self.default_image_width}]]"
        return f"![[{clean_path}]]"

    def _convert_link(self, match, root_path: Path) -> str:
        """Convert a DokuWiki link to Markdown format."""
        link = match.group(1)
        text = match.group(2) if len(match.groups()) > 1 else None
        
        # Handle external links
        if any(prefix in link for prefix in ['http://', 'https://']):
            return f"[{text or link}]({link})"
        
        # Handle internal links
        parts = link.split(':')
        filename = parts[-1]
        
        # Handle heading anchors
        if '#' in filename:
            filename, heading = filename.split('#', 1)
            if text:
                return f"[[{filename}#{heading}|{text}]]"
            return f"[[{filename}#{heading}]]"
        
        if text and text.lower() != filename.lower():
            return f"[[{filename}|{text}]]"
        return f"[[{filename}]]"