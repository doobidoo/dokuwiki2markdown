"""Text formatting conversion for DokuWiki to Markdown."""

import re
from typing import Dict, List, Tuple

class FormattingConverter:
    """Converts DokuWiki text formatting to Markdown."""

    def convert(self, content: str) -> str:
        """Convert DokuWiki formatting to Markdown."""
        conversions = [
            # Headings (in reverse order to prevent wrong replacements)
            (r'^====== (.+?) ======', r'# \1'),
            (r'^===== (.+?) =====', r'## \1'),
            (r'^==== (.+?) ====', r'### \1'),
            (r'^=== (.+?) ===', r'#### \1'),
            (r'^== (.+?) ==', r'##### \1'),
            (r'^= (.+?) =', r'###### \1'),
            
            # Text styling
            (r'\*\*(.+?)\*\*', r'**\1**'),  # Bold
            (r'//(.+?)//', r'*\1*'),         # Italic
            (r'__(.+?)__', r'<u>\1</u>'),    # Underline
            (r'<del>(.*?)</del>', r'~~\1~~'), # Strikethrough
            
            # Lists (preserve indentation)
            (r'^ {0,3}([*-]) ', r'\1 '),
            (r'^ {4,6}([*-]) ', r'    \1 '),
            (r'^ {7,9}([*-]) ', r'        \1 '),
            (r'^ {10,12}([*-]) ', r'            \1 '),
            
            # Remove line breaks
            (r'\\\\', ''),
            
            # Clean up multiple blank lines
            (r'\n\s*\n+', '\n\n')
        ]
        
        for pattern, replacement in conversions:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
            
        return content.strip()