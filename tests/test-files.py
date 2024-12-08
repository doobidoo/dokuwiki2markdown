# tests/test_tables.py
import unittest
from src.converters.tables import TableConverter

class TestTableConverter(unittest.TestCase):
    def setUp(self):
        self.converter = TableConverter()

    def test_simple_table(self):
        dokuwiki = "^ Header 1 ^ Header 2 ^\n| Cell 1 | Cell 2 |"
        expected = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1 | Cell 2 |"
        result = self.converter.convert(dokuwiki)
        self.assertEqual(result.strip(), expected.strip())

    def test_table_with_code(self):
        dokuwiki = "^ Header 1 ^ Header 2 ^\n| Cell 1 | <code>test</code> |"
        expected = "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1 | `test` |"
        result = self.converter.convert(dokuwiki)
        self.assertEqual(result.strip(), expected.strip())

# tests/test_formatting.py
import unittest
from src.converters.formatting import FormattingConverter

class TestFormattingConverter(unittest.TestCase):
    def setUp(self):
        self.converter = FormattingConverter()

    def test_bold(self):
        dokuwiki = "**bold text**"
        expected = "**bold text**"
        result = self.converter.convert(dokuwiki)
        self.assertEqual(result.strip(), expected)

    def test_italic(self):
        dokuwiki = "//italic text//"
        expected = "*italic text*"
        result = self.converter.convert(dokuwiki)
        self.assertEqual(result.strip(), expected)

# tests/test_media.py
import unittest
from pathlib import Path
from src.converters.media import MediaConverter

class TestMediaConverter(unittest.TestCase):
    def setUp(self):
        self.converter = MediaConverter()

    def test_image_link(self):
        dokuwiki = "{{image.png|caption}}"
        expected = "![[image.png | 300]]"
        result = self.converter.convert(dokuwiki, Path())
        self.assertEqual(result.strip(), expected)

    def test_external_link(self):
        dokuwiki = "[[http://example.com|Link Text]]"
        expected = "[Link Text](http://example.com)"
        result = self.converter.convert(dokuwiki, Path())
        self.assertEqual(result.strip(), expected)