"""Plugin conversion for DokuWiki to Markdown."""

""" Main Conversion Method:

Ordered processing of plugins to avoid conflicts
Modular design with separate methods for each plugin type

Supported Plugins:

Tag conversion ({{tag>...}} → #tag)
Radar charts (converted to comment blocks)
DrawIO diagrams (converted to image links)
Indexmenu (removed as not needed in Obsidian)
Include plugin (converted to Obsidian embeds)
WRAP plugin (converted to callouts)
CKEditor-specific syntax

Key Features:

Proper handling of nested content
Clean conversion of special characters
Preservation of content structure
Fallback handling for unsupported plugins """

import re
from typing import Optional, List

class PluginConverter:
    """Converts DokuWiki plugin syntax to Markdown."""

    def convert(self, content: str) -> str:
        """
        Convert DokuWiki plugin syntax to Markdown.
        
        Args:
            content: The DokuWiki content to convert
            
        Returns:
            The converted Markdown content
        """
        # Process plugins in specific order to avoid conflicts
        conversions = [
            self._convert_tags,
            self._convert_radar_charts,
            self._convert_drawio,
            self._convert_indexmenu,
            self._convert_include,
            self._convert_wrap_plugin,
            self._convert_ckgedit
        ]
        
        for conversion in conversions:
            content = conversion(content)
        
        return content

    def _convert_tags(self, content: str) -> str:
        """Convert DokuWiki tag syntax to Markdown tags."""
        def process_tag_match(match):
            # Extract tags from the tag syntax
            tags_text = match.group(1)
            # Use regex to split by spaces or handle quoted tags
            tags = re.findall(r'"([^"]+)"|(\S+)', tags_text)
            # Flatten the tuples and remove empty strings
            tags = [tag for group in tags for tag in group if tag]
            # Format as Markdown tags
            return ' '.join(f"#{tag.replace(' ', '_').replace('-', '_')}" for tag in tags)

        # Replace all tag syntax in the content
        return re.sub(r'\{\{tag>(.*?)\}\}', process_tag_match, content)


    def _convert_radar_charts(self, content: str) -> str:
        """Convert radar charts to a comment block since Obsidian doesn't support them directly."""
        return re.sub(
            r'<radar.*?>(.*?)</radar>',
            r'```comment\nRadar chart not supported in Obsidian:\n\1\n```',
            content,
            flags=re.DOTALL
        )

    def _convert_drawio(self, content: str) -> str:
        """Convert drawio diagrams to standard image links."""
        def process_drawio(match):
            path = match.group(1)
            filename = path.split(':')[-1]
            return f"![[{filename} | 300]]"
            
        return re.sub(r'\{\{drawio>(.*?)\}\}', process_drawio, content)

    def _convert_indexmenu(self, content: str) -> str:
        """Remove indexmenu plugin syntax as it's not needed in Obsidian."""
        return re.sub(r'\{\{indexmenu>([^|}]+)(?:\|(?:[^}]+))?\}\}', '', content)

    def _convert_include(self, content: str) -> str:
        """Convert include plugin to Obsidian embeds."""
        def process_include(match):
            type_of_include = match.group(1)  # page or section
            path = match.group(2)
            filename = path.split(':')[-1]
            return f"![[{filename}]]"
            
        return re.sub(r'\{\{(page|section)>([^|}]+)(?:\|(?:[^}]+))?\}\}', process_include, content)

    def _convert_wrap_plugin(self, content: str) -> str:
        """Convert WRAP plugin syntax to appropriate Markdown/HTML."""
        # Remove noprint wraps
        content = re.sub(r'<WRAP[ \t]*noprint(.*?)>((.|\n)*?)</WRAP>', r'\2', content)
        
        # Convert other wraps to callouts when appropriate
        def process_wrap(match):
            wrap_content = match.group(2).strip()
            if not wrap_content:
                return ''
            return f"\n> [!tip | cc-nt]\n> {wrap_content}\n"
            
        content = re.sub(r'<(WRAP|wrap|div|block)[ \t]*(.*?)>((.|\n)*?)</(WRAP|wrap|div|block)>', 
                        process_wrap, content)
        
        # Clean up any remaining wrap tags
        content = re.sub(r'<(WRAP|wrap)[ \t]*(.*?)>', '', content)
        content = re.sub(r'</(WRAP|wrap)[ \t]*(.*?)>', '', content)
        
        return content

    def _convert_ckgedit(self, content: str) -> str:
        """Convert CKEditor-specific syntax to Markdown/HTML."""
        # Convert font tags to emphasis
        return re.sub(r'<font.*?>((.|\n)*?)</font>', r'==\1==', content)

    def _remove_unsupported_plugins(self, content: str) -> str:
        """Remove any unsupported plugin syntax to keep the output clean."""
        # Add patterns for any other plugins that should be removed
        patterns = [
            r'\{\{(?!tag>|drawio>|page>|section>)[^}]+\}\}',  # Remove unknown plugin syntax
        ]
        
        for pattern in patterns:
            content = re.sub(pattern, '', content)
            
        return content