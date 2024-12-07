# DokuWiki to Obsidian Markdown Converter
This python script converts dokuwiki markup into markdown for Git or Obsidian

## Core Conversion Features

### Document Structure
- Converts DokuWiki headings (====== to =) to Markdown headings (# to ######)
- Preserves document hierarchy and structure
- Extracts and uses first heading as filename
- Maintains proper spacing and formatting

### Text Formatting
- Converts text styling (bold, italic, underline)
- Handles strikethrough text
- Preserves code blocks and inline code
- Processes multiline content
- Maintains original text formatting where possible

### Special Elements
- Converts DokuWiki tables to Markdown tables
- Handles collapsible sections
- Processes code blocks with syntax highlighting
- Converts note/warning/tip blocks to Obsidian callouts
- Supports mermaid diagrams
- Handles PlantUML diagrams
- Preserves special HTML blocks

### Links and Media
- Converts internal DokuWiki links to Obsidian wiki-links
- Processes external links with custom text
- Handles image links with captions
- Supports media file references
- Maintains link hierarchies
- Processes anchor links to headings

### File Management
- Copies and organizes media files
- Maintains folder structure
- Handles file naming conflicts
- Preserves file modification dates
- Supports incremental updates

## Technical Features

### Performance
- Concurrent file processing using ThreadPoolExecutor
- Efficient file handling with pathlib
- Optimized memory usage for large files
- Smart file update detection using content hashing
- Parallel media file copying

### Error Handling & Logging
- Comprehensive error logging system
- Detailed error messages and stack traces
- Progress tracking and reporting
- Warning system for potential issues
- Log file generation for debugging
- Console output for real-time progress

### Configuration Management
- Configurable source and destination paths
- Customizable media folder locations
- Adjustable processing parameters
- Configurable image default sizes
- Thread pool size configuration
- Logging level configuration

### Robustness
- Input validation for all paths
- UTF-8 encoding support
- Error recovery mechanisms
- Automatic folder creation
- Skip mechanism for unchanged files
- Protection against data loss

### Development Features
- Type hints for better code maintenance
- Comprehensive documentation
- Unit test support
- Custom exception handling
- Modular design for easy extension
- Clear separation of concerns

## Administrative Features
- Progress tracking for large conversions
- Summary reports of conversions
- Statistics on processed files
- Conversion time tracking
- Error rate monitoring
- Success/failure logging

This converter is designed to handle complex DokuWiki installations while providing reliable, efficient, and maintainable conversion to Obsidian markdown format. It's particularly suited for large wikis with complex formatting and media requirements.