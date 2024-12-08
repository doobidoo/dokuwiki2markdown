"""Table conversion module for DokuWiki to Markdown."""

import re
from typing import List

class TableConverter:
    """Converts DokuWiki tables to Markdown format."""

    def convert(self, content: str) -> str:
        """Convert DokuWiki tables to Markdown tables."""
        # Replace escaped pipes before processing
        content = content.replace('/%%|%%/g', '\\u0001')
        
        # Split content into blocks (table vs non-table)
        blocks = self._split_into_blocks(content)
        markdown_blocks = []
        
        for block in blocks:
            if self._is_table_block(block):
                markdown_blocks.append(self._convert_table(block))
            else:
                markdown_blocks.append(block)
                
        return '\n'.join(markdown_blocks)

    def _split_into_blocks(self, content: str) -> List[str]:
        """Split content into table and non-table blocks."""
        blocks = []
        current_block = []
        lines = content.split('\n')
        in_table = False
        
        for line in lines:
            is_table_line = line.strip().startswith('^') or line.strip().startswith('|')
            
            if is_table_line != in_table:
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
                in_table = is_table_line
                
            current_block.append(line)
            
        if current_block:
            blocks.append('\n'.join(current_block))
            
        return blocks

    def _is_table_block(self, block: str) -> bool:
        """Check if a block is a table block."""
        first_line = block.split('\n')[0].strip()
        return first_line.startswith('^') or first_line.startswith('|')

    def _convert_table(self, table_block: str) -> str:
        """Convert a DokuWiki table block to Markdown."""
        lines = table_block.split('\n')
        markdown_lines = []
        header_row = lines[0].strip().startswith('^')
        
        for i, line in enumerate(lines):
            if not line.strip():
                continue
                
            # Split cells and process content
            cells = re.split(r'[\^|]', line.strip('|^'))
            cells = [self._process_cell_content(cell) for cell in cells if cell]
            
            # Create table row
            row = f"| {' | '.join(cells)} |"
            markdown_lines.append(row)
            
            # Add separator row after headers
            if i == 0 and header_row:
                markdown_lines.append(f"|{'|'.join(['---' for _ in cells])}|")
        
        return '\n'.join(markdown_lines)

    def _process_cell_content(self, cell: str) -> str:
        """Process the content of a table cell."""
        # Handle linebreaks in cells by replacing them with <br>
        cell = cell.replace('\n', '<br>')
        
        # Handle code blocks in cells
        cell = re.sub(r'<code.*?>(.*?)</code>', r'`\1`', cell)
        
        # Restore escaped pipes
        cell = cell.replace('\\u0001', '\\|')
        
        # Clean up whitespace while preserving intentional spacing
        cell = re.sub(r'^\s+|\s+$', '', cell)
        
        return cell