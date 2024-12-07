#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DokuWiki to Markdown Converter
-----------------------------
A script to convert DokuWiki markup files to Obsidian-compatible markdown files.

Improvements made:
1. Added proper logging instead of print statements
2. Implemented proper error handling
3. Added configuration management
4. Improved code organization with classes
5. Added type hints
6. Added docstrings
7. Added progress tracking
8. Added concurrent processing for better performance
"""

import os
import re
import hashlib
import shutil
import urllib.parse
import uuid
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('converter.log'),
        logging.StreamHandler()
    ]
)

@dataclass
class ConverterConfig:
    """Configuration settings for the converter."""
    source_folder: Path
    destination_folder: Path
    media_folder: str = 'media'
    default_image_width: int = 300
    max_workers: int = 4

class ConversionError(Exception):
    """Custom exception for conversion errors."""
    pass

class DokuWikiConverter:
    """Main converter class for DokuWiki to Markdown conversion."""
    
    def __init__(self, config: ConverterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._validate_paths()

    def _validate_paths(self) -> None:
        """Validate that source and destination paths exist and are accessible."""
        if not self.config.source_folder.exists():
            raise ValueError(f"Source folder does not exist: {self.config.source_folder}")
        
        # Create destination folder if it doesn't exist
        self.config.destination_folder.mkdir(parents=True, exist_ok=True)

    def convert_file(self, dokuwiki_path: Path) -> Optional[Tuple[Path, str]]:
        """Convert a single DokuWiki file to Markdown."""
        try:
            with dokuwiki_path.open('r', encoding='utf-8') as f:
                content = f.read()

            title = self._extract_first_heading(content)
            converted_content = self._convert_syntax(content, dokuwiki_path.parent)
            
            rel_path = dokuwiki_path.relative_to(self.config.source_folder / 'pages')
            obsidian_folder = self.config.destination_folder / rel_path.parent
            obsidian_path = obsidian_folder / f"{title}.md"

            return obsidian_path, converted_content

        except Exception as e:
            self.logger.error(f"Error converting file {dokuwiki_path}: {str(e)}")
            return None

    def process_all_files(self) -> None:
        """Process all DokuWiki files in parallel."""
        try:
            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for file_path in (self.config.source_folder / 'pages').rglob('*.txt'):
                    futures.append(executor.submit(self.convert_file, file_path))

                for future in futures:
                    result = future.result()
                    if result:
                        obsidian_path, content = result
                        self._write_file(obsidian_path, content)

            self._copy_media_files()
            
        except Exception as e:
            self.logger.error(f"Error processing files: {str(e)}")
            raise

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file if necessary."""
        path.parent.mkdir(parents=True, exist_ok=True)
        
        if not self._should_skip_write(path, content):
            path.write_text(content, encoding='utf-8')
            self.logger.info(f"Wrote file: {path}")

    def _should_skip_write(self, path: Path, new_content: str) -> bool:
        """Determine if file should be skipped based on content hash."""
        if not path.exists():
            return False

        existing_hash = hashlib.md5(path.read_text(encoding='utf-8').encode()).hexdigest()
        new_hash = hashlib.md5(new_content.encode()).hexdigest()
        
        return existing_hash == new_hash

    def _copy_media_files(self) -> None:
        """Copy media files from DokuWiki to Obsidian."""
        media_source = self.config.source_folder / self.config.media_folder
        media_dest = self.config.destination_folder / self.config.media_folder

        if not media_source.exists():
            self.logger.warning(f"Media source folder does not exist: {media_source}")
            return

        for file_path in media_source.rglob('*'):
            if file_path.is_file():
                rel_path = file_path.relative_to(media_source)
                dest_path = media_dest / rel_path
                
                if not dest_path.exists():
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(file_path, dest_path)
                    self.logger.info(f"Copied media file: {rel_path}")

    @staticmethod
    def _extract_first_heading(content: str) -> str:
        """Extract the first heading from DokuWiki content."""
        match = re.search(r'====== (.+?) ======', content)
        return match.group(1) if match else "Untitled"

    def _convert_syntax(self, content: str, root_path: Path) -> str:
        """Convert DokuWiki syntax to Markdown/Obsidian syntax."""
        # Preserve special blocks
        preserved_blocks = self._preserve_special_blocks(content)
        
        # Apply conversions
        content = self._convert_headings(content)
        content = self._convert_links(content, root_path)
        content = self._convert_tables(content)
        content = self._convert_formatting(content)
        content = self._convert_plugins(content)
        
        # Restore preserved blocks
        content = self._restore_special_blocks(content, preserved_blocks)
        
        return content.strip()

    def _preserve_special_blocks(self, content: str) -> Dict[str, str]:
        """Preserve special blocks by replacing them with unique identifiers."""
        preserved = {}
        
        # Define patterns for special blocks
        patterns = {
            'code': r'(<code.*?>.*?</code>)',
            'note': r'(<note.*?>.*?</note>)',
            'mermaid': r'(<mermaid.*?>.*?</mermaid>)',
            'uml': r'(<uml.*?>.*?</uml>)'
        }
        
        for block_type, pattern in patterns.items():
            matches = re.finditer(pattern, content, re.DOTALL)
            for match in matches:
                uid = str(uuid.uuid4())
                preserved[uid] = match.group(0)
                content = content.replace(match.group(0), uid)
        
        return preserved

    def _restore_special_blocks(self, content: str, preserved_blocks: Dict[str, str]) -> str:
        """Restore preserved blocks by converting them to markdown format."""
        for uid, block in preserved_blocks.items():
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

    def _convert_headings(self, content: str) -> str:
        """Convert DokuWiki headings to Markdown headings."""
        patterns = [
            (r'^====== (.+?) ======', r'# \1'),
            (r'^===== (.+?) =====', r'## \1'),
            (r'^==== (.+?) ====', r'### \1'),
            (r'^=== (.+?) ===', r'#### \1'),
            (r'^== (.+?) ==', r'##### \1'),
            (r'^= (.+?) =', r'###### \1')
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
        
        return content

    def _convert_links(self, content: str, root_path: Path) -> str:
        """Convert DokuWiki links to Markdown/Obsidian links."""
        def convert_internal_link(match) -> str:
            link = match.group(1)
            text = match.group(2) if len(match.groups()) > 1 else None
            
            if any(prefix in link for prefix in ['http://', 'https://']):
                return f'[{text or link}]({link})'
            
            # Convert internal wiki links
            path_parts = link.split(':')
            link_path = Path(*path_parts)
            
            if text and text.lower() != link_path.name.lower():
                return f'[[{link_path.name}|{text}]]'
            return f'[[{link_path.name}]]'

        # Convert DokuWiki links
        content = re.sub(r'\[\[([^|]+)\|([^\]]+)\]\]', convert_internal_link, content)
        content = re.sub(r'\[\[([^\]]+)\]\]', convert_internal_link, content)
        
        return content

    def _convert_tables(self, content: str) -> str:
        """Convert DokuWiki tables to Markdown tables."""
        lines = content.split('\n')
        in_table = False
        markdown_lines = []
        
        for line in lines:
            if line.strip().startswith('^') or line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                # Convert DokuWiki table syntax to Markdown
                line = line.strip()
                line = re.sub(r'[\^|]', '|', line)
                if line.endswith('|'):
                    line = line[:-1]
                if line.startswith('|'):
                    line = line[1:]
                cells = [cell.strip() for cell in line.split('|')]
                markdown_lines.append('| ' + ' | '.join(cells) + ' |')
                
                # Add header separator
                if line.strip().startswith('^') and not any('---' in l for l in markdown_lines[-2:]):
                    markdown_lines.append('| ' + ' | '.join(['---' for _ in cells]) + ' |')
            else:
                in_table = False
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)

    def _convert_formatting(self, content: str) -> str:
        """Convert DokuWiki text formatting to Markdown."""
        # Bold
        content = re.sub(r'\*\*(.+?)\*\*', r'**\1**', content)
        # Italic
        content = re.sub(r'//(.+?)//', r'*\1*', content)
        # Underline
        content = re.sub(r'__(.+?)__', r'<u>\1</u>', content)
        # Strikethrough
        content = re.sub(r'<del>(.*?)</del>', r'~~\1~~', content)
        
        return content

    def _convert_plugins(self, content: str) -> str:
        """Convert DokuWiki plugin syntax."""
        # Remove indexmenu
        content = re.sub(r'\{\{indexmenu>([^|}]+)(?:\|(?:[^}]+))?\}\}', '', content)
        
        # Convert include plugin
        content = re.sub(r'\{\{(page|section)>([^|}]+)(?:\|(?:[^}]+))?\}\}', r'![\2]', content)
        
        return content

    def _convert_code_block(self, block: str) -> str:
        """Convert code blocks to markdown format."""
        match = re.search(r'<code.*?>(.*?)</code>', block, re.DOTALL)
        if match:
            code = match.group(1).strip()
            return f'\n```\n{code}\n```\n'
        return block

    def _convert_note_block(self, block: str) -> str:
        """Convert note blocks to Obsidian callouts."""
        match = re.search(r'<note(?:\s+(?P<type>tip|important|warning|caution))?\s*>(.*?)</note>', block, re.DOTALL)
        if match:
            note_type = match.group('type').upper() if match.group('type') else 'NOTE'
            content = match.group(2).strip()
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
        """Convert UML blocks to markdown format."""
        match = re.search(r'<uml.*?>(.*?)</uml>', block, re.DOTALL)
        if match:
            content = match.group(1).strip()
            return f'\n```plantuml\n{content}\n```\n'
        return block

def get_valid_path(prompt: str, must_exist: bool = False) -> Path:
    """
    Prompt for and validate a directory path.
    
    Args:
        prompt: The prompt to show to the user
        must_exist: Whether the path must already exist
    
    Returns:
        Path object of validated directory
    """
    while True:
        path_str = input(prompt).strip()
        
        # Handle empty input
        if not path_str:
            print("Please enter a path.")
            continue
            
        # Convert to Path object and resolve to absolute path
        try:
            path = Path(path_str).resolve()
        except Exception as e:
            print(f"Invalid path format: {e}")
            continue
            
        # Check if path exists when required
        if must_exist and not path.exists():
            print(f"Path does not exist: {path}")
            continue
            
        # For source folder, check if it has the required structure
        if must_exist and 'pages' not in [x.name for x in path.iterdir()]:
            print(f"Source folder must contain a 'pages' subdirectory: {path}")
            continue
            
        return path

def main():
    """Main entry point for the converter."""
    print("\nDokuWiki to Obsidian Markdown Converter")
    print("---------------------------------------\n")
    
    try:
        # Get source folder (must exist and have proper structure)
        source = get_valid_path(
            "Enter the path to DokuWiki's data folder (containing 'pages' subdirectory): ", 
            must_exist=True
        )
        
        # Get destination folder (will be created if doesn't exist)
        dest = get_valid_path(
            "Enter the destination path for Obsidian vault: "
        )
        
        print(f"\nConverting from: {source}")
        print(f"Converting to: {dest}\n")
        
        config = ConverterConfig(
            source_folder=source,
            destination_folder=dest
        )
        
        converter = DokuWikiConverter(config)
        converter.process_all_files()
        
        logging.info("Conversion completed successfully!")
        
    except Exception as e:
        logging.error(f"Conversion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()