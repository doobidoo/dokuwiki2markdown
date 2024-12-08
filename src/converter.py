"""Main converter class for DokuWiki to Markdown conversion."""

import logging
from pathlib import Path
from typing import Optional, Tuple
from concurrent.futures import ThreadPoolExecutor

from .config import ConverterConfig
from .converters.tables import TableConverter
from .converters.formatting import FormattingConverter
from .converters.media import MediaConverter
from .converters.plugins import PluginConverter
from .converters.special import SpecialBlockConverter
from .utils.file_handling import FileHandler  # Updated import
from .utils.sanitization import sanitize_filename

class DokuWikiConverter:
    """Main converter class for DokuWiki to Markdown conversion."""
    
    def __init__(self, config: ConverterConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize converters
        self.table_converter = TableConverter()
        self.formatting_converter = FormattingConverter()
        self.media_converter = MediaConverter(config.default_image_width)
        self.plugin_converter = PluginConverter()
        self.special_converter = SpecialBlockConverter()
        self.file_handler = FileHandler()  # Initialize FileHandler

    def convert_file(self, dokuwiki_path: Path) -> Optional[Tuple[Path, str]]:
        """Convert a single DokuWiki file to Markdown."""
        try:
            with dokuwiki_path.open('r', encoding='utf-8') as f:
                content = f.read()

            # Extract title and convert content
            title = self._extract_first_heading(content)
            converted_content = self._convert_content(content, dokuwiki_path.parent)
            
            # Create output path
            rel_path = dokuwiki_path.relative_to(self.config.source_folder / 'pages')
            safe_parts = [sanitize_filename(part) for part in rel_path.parent.parts]
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
                            if FileHandler.should_update_file(obsidian_path, content):  # Use class method
                                obsidian_path.parent.mkdir(parents=True, exist_ok=True)
                                obsidian_path.write_text(content, encoding='utf-8')
                                processed_count += 1
                                self.logger.info(f"Processed {processed_count}/{total_files}: {obsidian_path}")
                            else:
                                self.logger.info(f"Skipped unchanged file: {obsidian_path}")
                    except Exception as e:
                        error_count += 1
                        self.logger.error(f"Error processing file: {str(e)}")

            self.logger.info(f"\nConversion Summary:")
            self.logger.info(f"Total files found: {total_files}")
            self.logger.info(f"Successfully processed: {processed_count}")
            self.logger.info(f"Errors encountered: {error_count}")

            # Use FileHandler for copying media files
            FileHandler.copy_media_files(self.config.source_folder, self.config.destination_folder)
            
        except Exception as e:
            self.logger.error(f"Error processing files: {str(e)}")
            raise

    def _extract_first_heading(self, content: str) -> str:
        """Extract and sanitize the first heading from DokuWiki content."""
        import re
        match = re.search(r'====== (.+?) ======', content)
        title = match.group(1) if match else "Untitled"
        return sanitize_filename(title)

    def _convert_content(self, content: str, root_path: Path) -> str:
        """Convert DokuWiki content to Markdown/Obsidian format."""
        # Preserve special blocks first
        content = self.special_converter.preserve_blocks(content)
        
        # Apply conversions
        content = self.formatting_converter.convert(content)
        content = self.table_converter.convert(content)
        content = self.media_converter.convert(content, root_path)
        content = self.plugin_converter.convert(content)
        
        # Restore special blocks last
        content = self.special_converter.restore_blocks(content)
        
        return content.strip()