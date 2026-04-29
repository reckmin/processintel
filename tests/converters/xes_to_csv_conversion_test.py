import os
import unittest
import xml.etree.ElementTree as ET

from app.converters.xes_to_csv_converter import XesToCsvConverter


class XesToCsvConversionTest(unittest.TestCase):
    def setUp(self):
        """Set up before running tests."""
        self.xes_to_csv_converter = XesToCsvConverter()
        self.test_xes_dir = os.path.join(os.path.dirname(__file__), "..", "testxes")
        self.sample_xes_path = os.path.join(self.test_xes_dir, "simple_log.xes")

    def test_xes_to_csv_conversion(self):
        """Test the XES to CSV conversion."""
        with open(self.sample_xes_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)
            df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        self.assertIsNotNone(df)
        self.assertIn("concept:name", df.columns)
        self.assertIn("case:concept:name", df.columns)
        self.assertIn("time:timestamp", df.columns)
        self.assertEqual(len(df), 14)

    def test_xes_to_csv_conversion_rejects_empty_xes(self):
        """Test that converting an empty XES file raises a ValueError."""
        xes_content = """<?xml version="1.0" encoding="UTF-8" ?>
<log>
</log>"""
        root = ET.fromstring(xes_content)
        tree = ET.ElementTree(root)

        with self.assertRaises(ValueError) as context:
            self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        self.assertEqual(str(context.exception), "The XES file contains no event data.")

    def test_xes_to_csv_conversion_extracts_case_ids(self):
        """Test that case IDs are correctly extracted."""
        with open(self.sample_xes_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)
        df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        case_ids = df["case:concept:name"].unique().tolist()
        self.assertIn("case1", case_ids)
        self.assertIn("case2", case_ids)
        self.assertEqual(len(case_ids), 5)

    def test_xes_to_csv_conversion_extracts_activities(self):
        """Test that activities are correctly extracted."""
        with open(self.sample_xes_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)
        df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        activities = df["concept:name"].unique().tolist()
        self.assertIn("activity1", activities)
        self.assertIn("activity2", activities)
        self.assertIn("activity3", activities)

    def test_xes_to_csv_conversion_with_various_types(self):
        """Test XES file with different attribute types."""
        various_types_path = os.path.join(self.test_xes_dir, "various_types.xes")
        with open(various_types_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)

        df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        self.assertEqual(len(df), 16)
        self.assertIn("cost", df.columns)
        self.assertIn("duration", df.columns)
        self.assertIn("completed", df.columns)
        self.assertEqual(df["cost"].iloc[0], 100)
        self.assertEqual(df["duration"].iloc[0], 1.5)
        self.assertEqual(df["completed"].iloc[0], True)

    def test_xes_to_csv_conversion_ignores_empty_trace(self):
        """Test that empty traces are ignored during conversion."""
        xes_content = """<?xml version="1.0" encoding="UTF-8" ?>
<log>
    <trace>
        <string key="concept:name" value="empty_case"/>
    </trace>
    <trace>
        <string key="concept:name" value="case1"/>
        <event>
            <string key="concept:name" value="activity1"/>
        </event>
    </trace>
</log>"""
        root = ET.fromstring(xes_content)
        tree = ET.ElementTree(root)

        df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)
        self.assertEqual(len(df), 1)

    def test_xes_to_csv_conversion_include_only_essential_attributes(self):
        """Test the XES to CSV conversion selecting only essential attributes."""
        multiple_attributes_path = os.path.join(
            self.test_xes_dir, "multiple_attributes.xes"
        )
        with open(multiple_attributes_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)
            df = self.xes_to_csv_converter.convert(tree, include_all_attributes=False)

        self.assertIsNotNone(df)
        self.assertListEqual(
            list(df.columns),
            ["case_id", "activity", "timestamp"],
        )

    def test_xes_to_csv_conversion_include_all_attributes(self):
        """Test the XES to CSV conversion keeps all columns and its original names."""
        multiple_attributes_path = os.path.join(
            self.test_xes_dir, "multiple_attributes.xes"
        )
        with open(multiple_attributes_path, "r", encoding="utf-8") as xes_file:
            tree = ET.parse(xes_file)
            df = self.xes_to_csv_converter.convert(tree, include_all_attributes=True)

        self.assertIsNotNone(df)
        self.assertEqual(len(df.columns), 7)
        self.assertIn("case:concept:name", df.columns)
        self.assertIn("time:timestamp", df.columns)
        self.assertIn("concept:name", df.columns)
        self.assertIn("lifecycle:transition", df.columns)


if __name__ == "__main__":
    unittest.main()
