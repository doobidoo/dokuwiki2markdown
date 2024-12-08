"""Table conversion module for DokuWiki to Markdown."""

import re
from typing import List

class TableConverter:
    """Converts DokuWiki tables to Markdown format."""

    def convert(self, content: str) -> str:
        """ Replace escaped pipes before splitting"""
        content = content.replace('/%%\|%%/g', '\\u0001')

        """Convert DokuWiki tables to Markdown tables."""
        lines = content.split('\n')
        markdown_lines = []
        in_table = False
        header_row = False
        

        for line in lines:
            if line.strip().startswith('^') or line.strip().startswith('|'):
                if not in_table:
                    in_table = True
                    header_row = line.strip().startswith('^')

                # Split cells and process content
                cells = re.split(r'[\^|]', line.strip('|^'))
                cells = [self._process_cell_content(cell) for cell in cells if cell.strip()]
                
                # Create table row
                row = f"| {' | '.join(cells)} |"
                markdown_lines.append(row)
                
                # Add separator row after headers
                if header_row:
                    markdown_lines.append(f"|{'|'.join(['---' for _ in cells])}|")
                    header_row = False
            else:
                if in_table:
                    markdown_lines.append('')  # Add empty line after table
                    in_table = False
                markdown_lines.append(line)
        
        return '\n'.join(markdown_lines)

    def _process_cell_content(self, cell: str) -> str:
        """Process the content of a table cell."""
        # Handle linebreaks in cells by replacing them with <br>
        cell = cell.replace('\n', '<br>')
        
        # Handle code blocks in cells
        cell = re.sub(r'<code.*?>(.*?)</code>', r'```\1```', cell)
        
        # Restore escaped pipes
        cell = cell.replace('\\u0001', '\|')
        
        # Clean up whitespace while preserving intentional spacing
        cell = re.sub(r'^\s+|\s+$', '', cell)
        
        return cell