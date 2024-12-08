#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DokuWiki to Markdown Converter
Entry point for the conversion process
"""

import logging
from pathlib import Path
from src.config import ConverterConfig
from src.converter import DokuWikiConverter
from src.utils.file_handling import FileHandler  # Updated import

def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('converter.log'),
            logging.StreamHandler()
        ]
    )

def main():
    """Main entry point for the converter."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("\nDokuWiki to Obsidian Markdown Converter")
    print("---------------------------------------\n")
    
    try:
        # Get source folder (must exist and have proper structure)
        source = FileHandler.get_valid_path(
            "Enter the path to DokuWiki's data folder (containing 'pages' subdirectory): ", 
            must_exist=True
        )
        
        # Get destination folder (will be created if doesn't exist)
        dest = FileHandler.get_valid_path(
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
        
        logger.info("Conversion completed successfully!")
        
    except Exception as e:
        logger.error(f"Conversion failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()