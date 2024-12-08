"""Special block conversion for DokuWiki to Markdown."""

import re
import uuid
from typing import Dict, Optional

class SpecialBlockConverter:
    """Handles conversion of special blocks like code, notes, mermaid, and UML."""

    def __init__(self):
        self._preserved_blocks: Dict[str, str] = {}

    def preserve_blocks(self, content: str) -> str:
        """
        Preserve special blocks by replacing them with unique identifiers.
        
        Args:
            content: The content to process
            
        Returns:
            Content with special blocks replaced by placeholders
        """
        self._preserved_blocks.clear()
        
        # Define patterns for special blocks
        patterns = {
            'code': r'(<code.*?>.*?</code>)',
            'note': r'(<note.*?>.*?</note>)',
            'mermaid': r'(<mermaid.*?>.*?</mermaid>)',
            'uml': r'(<uml.*?>.*?</uml>)'
        }
        
        for block_type, pattern in patterns.items():
            content = self._preserve_pattern(content, pattern)
            
        return content

    def restore_blocks(self, content: str) -> str:
        """
        Restore preserved blocks with their converted markdown equivalents.
        
        Args:
            content: Content with preserved block placeholders
            
        Returns:
            Content with special blocks converted to markdown
        """
        for uid, block in self._preserved_blocks.items():
            if '<code' in block:
                converted = self._convert_code_block(block)
            elif '<note' in block:
                converted = self._convert_note_block(block)
            elif '<mermaid' in block:
                converted = self._convert_mermaid_block(block)
            elif '<uml' in block:
                converted = self._convert_uml_block(block)
            else:
                converted = block
            content = content.replace(uid, converted)
            
        return content

    def _preserve_pattern(self, content: str, pattern: str) -> str:
        """Replace pattern matches with unique identifiers."""
        matches = re.finditer(pattern, content, re.DOTALL)
        for match in matches:
            uid = str(uuid.uuid4())
            self._preserved_blocks[uid] = match.group(0)
            content = content.replace(match.group(0), uid)
        return content

    def _convert_code_block(self, block: str) -> str:
        """Convert code blocks to markdown format."""
        match = re.search(r'<code(?:\s+(\w+))?\s*>(.*?)</code>', block, re.DOTALL)
        if match:
            language = match.group(1) or ''
            code = match.group(2).strip()
            return f'\n```{language}\n{code}\n```\n'
        return block

    def _convert_note_block(self, block: str) -> str:
        """Convert note blocks to Obsidian callouts."""
        match = re.search(
            r'<note(?:\s+(?P<type>tip|important|warning|caution))?\s*>(?P<content>.*?)</note>',
            block,
            re.DOTALL
        )
        if match:
            note_type = match.group('type').upper() if match.group('type') else 'NOTE'
            content = match.group('content').strip()
            # Format content for callout - indent all lines
            content = '\n> '.join(content.split('\n'))
            return f'\n> [!{note_type}]\n> {content}\n'
        return block

    def _convert_mermaid_block(self, block: str) -> str:
        """Convert mermaid blocks to markdown format."""
        match = re.search(r'<mermaid.*?>(.*?)</mermaid>', block, re.DOTALL)
        if match:
            content = match.group(1).strip()
            return f'\n```mermaid\n{content}\n```\n'
        return block

    def _convert_uml_block(self, block: str) -> str:
        """Convert UML blocks to plantuml format."""
        match = re.search(r'<uml.*?>(.*?)</uml>', block, re.DOTALL)
        if match:
            content = match.group(1).strip()
            return f'\n```plantuml\n{content}\n```\n'
        return block