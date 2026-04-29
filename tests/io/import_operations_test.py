import unittest
import os
import xml.etree.ElementTree as ET

from app.io_operations.import_operations import ImportOperations


class TestImportOperations(unittest.TestCase):

    def setUp(self):
        """Set up before runnign tests."""
        self.importer = ImportOperations()
        self.test_xes_dir = os.path.join(os.path.dirname(__file__), "..", "testxes")
        self.sample_xes_path = os.path.join(self.test_xes_dir, "simple_log.xes")

    def test_read_xes_returns_element_tree(self):
        """Test that reading XES file returns an ElementTree."""
        xes_tree = self.importer.read_xes(self.sample_xes_path)

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertTrue(xes_tree.getroot().tag.endswith("log"))

    def test_read_xes_with_namespace_returns_element_tree(self):
        """Test reading XES file with namespace."""
        xes_path = os.path.join(self.test_xes_dir, "with_namespace.xes")
        xes_tree = self.importer.read_xes(xes_path)

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertTrue(xes_tree.getroot().tag.endswith("log"))

    def test_read_xes_rejects_invalid_file(self):
        """Test that invalid XES file is rejected."""
        invalid_xes_content = """<?xml version="1.0" encoding="UTF-8" ?>
<log>
    <trace>
        <string key="concept:name" value="case1">
    </trace>
</log>"""
        invalid_xes_path = os.path.join(self.test_xes_dir, "invalid.xes")
        with open(invalid_xes_path, "w", encoding="utf-8") as xes_file:
            xes_file.write(invalid_xes_content)

        with self.assertRaises(ET.ParseError):
            self.importer.read_xes(invalid_xes_path)


if __name__ == "__main__":
    unittest.main()
