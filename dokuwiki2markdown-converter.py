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
        
        # Restore preserved blocks
        content = self._restore_special_blocks(content, preserved_blocks)
        
        return content.strip()

    # ... [Rest of the conversion methods would go here]

def main():
    """Main entry point for the converter."""
    try:
        config = ConverterConfig(
            source_folder=Path('path/to/source'),
            destination_folder=Path('path/to/destination')
        )
        
        converter = DokuWikiConverter(config)
        converter.process_all_files()
        
        logging.info("Conversion completed successfully!")
        
    except Exception as e:
        logging.error(f"Conversion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()