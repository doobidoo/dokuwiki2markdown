# src/__init__.py
"""DokuWiki to Markdown converter package."""
from .converter import DokuWikiConverter
from .config import ConverterConfig

__version__ = '1.0.0'
__all__ = ['DokuWikiConverter', 'ConverterConfig']
