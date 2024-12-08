"""Filename sanitization utilities."""

import re
from typing import Set

def sanitize_filename(filename: str) -> str:
    """
    Sanitize a filename to be compatible with all operating systems.
    
    Args:
        filename: The filename to sanitize
        
    Returns:
        A sanitized filename safe for all operating systems
    """
    # Characters not allowed in various operating systems
    forbidden_chars = ['<', '>', ':', '"', '/', '\\', '|', '?', '*']
    
    # Windows reserved names
    reserved_names: Set[str] = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    # Clean the filename
    clean_name = filename.strip()
    
    # Replace forbidden characters with a dash
    for char in forbidden_chars:
        clean_name = clean_name.replace(char, '-')
    
    # Remove multiple dashes and dots
    clean_name = re.sub(r'[-\s]+', '-', clean_name)
    clean_name = re.sub(r'\.+', '.', clean_name)
    
    # Remove leading/trailing dashes and dots
    clean_name = clean_name.strip('.-')
    
    # Handle Windows reserved names
    if clean_name.upper() in reserved_names:
        clean_name = f"_{clean_name}"
    
    # Ensure the filename isn't empty
    if not clean_name:
        clean_name = "untitled"
    
    # Truncate filename if it's too long (Windows has a 255 character limit)
    max_length = 255
    if len(clean_name) > max_length:
        base_name = clean_name.rsplit('.', 1)[0]
        extension = clean_name.rsplit('.', 1)[1] if '.' in clean_name else ''
        max_base_length = max_length - len(extension) - 1
        clean_name = f"{base_name[:max_base_length]}.{extension}" if extension else base_name[:max_length]
    
    return clean_name