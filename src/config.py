"""Configuration management for the DokuWiki to Markdown converter."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class ConverterConfig:
    """Configuration settings for the converter."""
    source_folder: Path
    destination_folder: Path
    media_folder: str = 'media'
    default_image_width: int = 300
    max_workers: int = 4
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        self.source_folder = Path(self.source_folder)
        self.destination_folder = Path(self.destination_folder)
        
        if not self.source_folder.exists():
            raise ValueError(f"Source folder does not exist: {self.source_folder}")
        
        if not (self.source_folder / 'pages').exists():
            raise ValueError(f"Source folder must contain a 'pages' subdirectory: {self.source_folder}")
        
        # Create destination folder if it doesn't exist
        self.destination_folder.mkdir(parents=True, exist_ok=True)