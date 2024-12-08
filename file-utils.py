"""File handling utilities for the DokuWiki to Markdown converter."""

import os
from pathlib import Path
import shutil
import hashlib
from typing import Optional

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

def copy_media_files(source_folder: Path, dest_folder: Path, media_dir: str = 'media') -> None:
    """
    Copy media files from source to destination.
    
    Args:
        source_folder: Source directory containing media files
        dest_folder: Destination directory for media files
        media_dir: Name of the media directory
    """
    media_source = source_folder / media_dir
    media_dest = dest_folder / media_dir

    if not media_source.exists():
        return

    for file_path in media_source.rglob('*'):
        if file_path.is_file():
            rel_path = file_path.relative_to(media_source)
            dest_path = media_dest / rel_path
            
            if not dest_path.exists():
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)

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
        existing_hash = hashlib.md5(file_path.read_text(encoding='utf-8').encode()).hexdigest()
        new_hash = hashlib.md5(new_content.encode()).hexdigest()
        return existing_hash != new_hash
    except Exception:
        return True  # If there's any error reading the file, assume it needs updating