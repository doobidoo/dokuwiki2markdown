"""File handling utilities for the DokuWiki to Markdown converter."""

""" Class Structure:

Organized as a proper class with static methods
Better encapsulation of file handling operations

Additional Methods:

should_update_file: Checks if content has changed using MD5 hashing
copy_media_files: Handles media file transfers with directory structure preservation
ensure_directory: Creates directories as needed
clean_directory: Utility for cleaning directories

Enhanced Features:

Better error handling throughout
Progress feedback for file operations
Preservation of file timestamps
Directory structure maintenance
"""

import os
import shutil
import hashlib
from pathlib import Path
from typing import Optional

class FileHandler:
    """Handles file operations for the converter."""

    @staticmethod
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

    @staticmethod
    def should_update_file(file_path: Path, new_content: str) -> bool:
        """
        Check if a file should be updated based on content hash.
        
        Args:
            file_path: Path to the existing file
            new_content: New content to compare against
            
        Returns:
            True if file should be updated, False otherwise
        """
        if not file_path.exists():
            return True

        try:
            # Calculate MD5 hash of existing content
            with file_path.open('r', encoding='utf-8') as f:
                existing_hash = hashlib.md5(f.read().encode()).hexdigest()
            
            # Calculate MD5 hash of new content
            new_hash = hashlib.md5(new_content.encode()).hexdigest()
            
            # Return True if content has changed
            return existing_hash != new_hash
        except Exception:
            # If there's any error reading the file, assume it needs updating
            return True

    @staticmethod
    def copy_media_files(source_folder: Path, dest_folder: Path, media_dir: str = 'media') -> None:
        """
        Copy media files from source to destination, preserving directory structure.
        
        Args:
            source_folder: Source directory containing media files
            dest_folder: Destination directory for media files
            media_dir: Name of the media directory
        """
        media_source = source_folder / media_dir
        media_dest = dest_folder / media_dir

        if not media_source.exists():
            print(f"Warning: Media source folder does not exist: {media_source}")
            return

        try:
            # Walk through all files in the media directory
            for file_path in media_source.rglob('*'):
                if file_path.is_file():
                    # Calculate relative path to maintain directory structure
                    rel_path = file_path.relative_to(media_source)
                    dest_path = media_dest / rel_path
                    
                    # Create destination directory if it doesn't exist
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Copy file if it doesn't exist or has been modified
                    if not dest_path.exists() or (
                        file_path.stat().st_mtime > dest_path.stat().st_mtime
                    ):
                        shutil.copy2(file_path, dest_path)
                        print(f"Copied media file: {rel_path}")

        except Exception as e:
            print(f"Error copying media files: {str(e)}")

    @staticmethod
    def ensure_directory(path: Path) -> None:
        """
        Ensure a directory exists, creating it if necessary.
        
        Args:
            path: Path to the directory to create
        """
        path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def clean_directory(path: Path) -> None:
        """
        Remove all files in a directory but keep the directory.
        
        Args:
            path: Path to the directory to clean
        """
        if path.exists():
            for item in path.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)