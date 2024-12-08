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
            
            # Create sanitized folder names for each part of the path
            rel_path = dokuwiki_path.relative_to(self.config.source_folder / 'pages')
            safe_parts = [self._sanitize_filename(part) for part in rel_path.parent.parts]
            obsidian_folder = self.config.destination_folder.joinpath(*safe_parts)
            obsidian_path = obsidian_folder / f"{title}.md"

            self.logger.info(f"Converting {dokuwiki_path} to {obsidian_path}")
            return obsidian_path, converted_content

        except Exception as e:
            self.logger.error(f"Error converting file {dokuwiki_path}: {str(e)}")
            return None

    def process_all_files(self) -> None:
        """Process all DokuWiki files in parallel."""
        try:
            # Get list of all .txt files in pages directory
            pages_dir = self.config.source_folder / 'pages'
            if not pages_dir.exists():
                raise ValueError(f"Pages directory not found: {pages_dir}")
                
            files = list(pages_dir.rglob('*.txt'))
            total_files = len(files)
            
            if total_files == 0:
                self.logger.warning(f"No .txt files found in {pages_dir}")
                return
                
            self.logger.info(f"Found {total_files} files to process")
            processed_count = 0
            error_count = 0

            with ThreadPoolExecutor(max_workers=self.config.max_workers) as executor:
                futures = []
                for file_path in files:
                    futures.append(executor.submit(self.convert_file, file_path))

                for future in futures:
                    try:
                        result = future.result()
                        if result:
                            obsidian_path, content = result
                            try:
                                self._write_file(obsidian_path, content)
                                processed_count += 1
                                self.logger.info(f"Processed {processed_count}/{total_files}: {obsidian_path}")
                            except Exception as e:
                                error_count += 1
                                self.logger.error(f"Error writing file {obsidian_path}: {str(e)}")
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"Error processing file: {str(e)}")

            self.logger.info(f"\nConversion Summary:")
            self.logger.info(f"Total files found: {total_files}")
            self.logger.info(f"Successfully processed: {processed_count}")
            self.logger.info(f"Errors encountered: {error_count}")

            self._copy_media_files()
            
        except Exception as e:
            self.logger.error(f"Error processing files: {str(e)}")
            raise

    def _write_file(self, path: Path, content: str) -> None:
        """Write content to file if necessary."""
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if file exists and content is different
            if path.exists():
                existing_hash = hashlib.md5(path.read_text(encoding='utf-8').encode()).hexdigest()
                new_hash = hashlib.md5(content.encode()).hexdigest()
                if existing_hash == new_hash:
                    self.logger.info(f"Skipping unchanged file: {path}")
                    return
                    
            # Write the file
            path.write_text(content, encoding='utf-8')
            self.logger.info(f"Written file: {path}")
            
        except Exception as e:
            self.logger.error(f"Error writing file {path}: {str(e)}")
            raise

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
    def _sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to be compatible with all operating systems.
        
        Args:
            filename: The original filename
            
        Returns:
            A sanitized filename safe for all operating systems
        """
        # Characters not allowed in various operating systems
        forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
        
        # Replace forbidden characters with a safe alternative
        for char in forbidden_chars:
            filename = filename.replace(char, '-')
            
        # Additional Windows filename restrictions
        filename = filename.rstrip('. ')  # Windows doesn't allow trailing dots or spaces
        
        # Handle reserved Windows filenames
        reserved_names = {
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        }
        if filename.upper() in reserved_names:
            filename = f"_{filename}"
            
        # Ensure filename isn't empty after sanitization
        if not filename.strip('-. '):
            filename = "untitled"
            
        return filename.strip()

    @staticmethod
    def _extract_first_heading(content: str) -> str:
        """Extract the first heading from DokuWiki content."""
        match = re.search(r'====== (.+?) ======', content)
        title = match.group(1) if match else "Untitled"
        return DokuWikiConverter._sanitize_filename(title)

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
        """Convert DokuWiki tables to Markdown tables with proper handling of inline code."""
        def process_cell_content(cell: str) -> str:
            # Handle code blocks in cells
            cell = re.sub(r'<code.*?>(.*?)</code>', r'`\1`', cell)
            # Escape pipes that aren't part of table structure
            cell = cell.replace('|', '\\|')
            return cell.strip()

        lines = content.split('\n')
        markdown_lines = []
        in_table = False
        header_row = False
        
        for line in lines:
            if line.strip().startswith('^') or line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    header_row = line.strip().startswith('^')

                # Split cells and process content
                cells = re.split(r'[\^|]', line.strip('|^'))
                cells = [process_cell_content(cell) for cell in cells if cell.strip()]
                
                # Create table row
                row = f"| {' | '.join(cells)} |"
                markdown_lines.append(row)
                
                # Add separator row after headers
                if header_row:
                    markdown_lines.append(f"|{'|'.join(['---' for _ in cells])}|")
                    header_row = False
            else:
                if in_table:
                    markdown_lines.append('')  # Add empty line after table
                    in_table = False
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)

    def _convert_tags(self, content: str) -> str:
        """Convert DokuWiki tags to Obsidian tags."""
        def process_tag_match(match):
            # Extract tags from the tag syntax
            tags_text = match.group(1)
            # Split by spaces and clean up each tag
            tags = re.findall(r'"([^"]+)"|(\S+)', tags_text)
            # Flatten the tuples and remove empty strings
            tags = [''.join(t) for t in tags if any(t)]
            # Format as Obsidian tags
            return ' '.join(f"#{tag.replace(' ', '_').replace('-', '_')}" for tag in tags)
            
        # Convert tag syntax
        content = re.sub(r'\{\{tag>(.*?)\}\}', process_tag_match, content)
        return content

    def _convert_media_link(self, match: re.Match) -> str:
        """Convert DokuWiki media links to Obsidian format."""
        path = match.group(1)
        caption = match.group(2) if len(match.groups()) > 1 else None
        
        # Handle image extensions
        image_exts = ['jpg', 'jpeg', 'png', 'svg', 'gif']
        is_image = any(ext in path.lower() for ext in image_exts)
        
        # Clean up the path
        path = path.split(':')[-1]  # Get last part of path
        path = re.sub(r'\?.*

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
, '', path)  # Remove query parameters
        
        if is_image:
            return f"![[{path} | 300]]"  # Use consistent image size
        else:
            return f"![[{path}]]"

    def _convert_plugins(self, content: str) -> str:
        """Convert DokuWiki plugin syntax."""
        # Handle radar charts - convert to code block with comment
        content = re.sub(
            r'<radar.*?>(.*?)</radar>',
            r'```comment\nRadar chart not supported in Obsidian:\n\1\n```',
            content,
            flags=re.DOTALL
        )
        
        # Handle drawio diagrams
        content = re.sub(
            r'\{\{drawio>(.*?)\}\}',
            lambda m: f"![[{m.group(1).split(':')[-1]} | 300]]",
            content
        )
        
        # Remove indexmenu
        content = re.sub(r'\{\{indexmenu>([^|}]+)(?:\|(?:[^}]+))?\}\}', '', content)
        
        # Convert include plugin
        content = re.sub(r'\{\{(page|section)>([^|}]+)(?:\|(?:[^}]+))?\}\}', r'![\2]', content)
        
        return content

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
        # Remove line breaks
        content = re.sub(r'\\\\', '', content)
        
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