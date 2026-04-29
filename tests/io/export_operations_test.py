import unittest
import pandas as pd
import xml.etree.ElementTree as ET
import tempfile
import streamlit as st
from app.io_operations.export_operations import ExportOperations


class TestExportOperations(unittest.TestCase):
    def setUp(self):
        """Set up before running tests."""
        self.exporter = ExportOperations()

    def test_export_to_csv_data_returns_csv_text(self):
        """Test that a dataframe is exported to CSV tex."""
        df = pd.DataFrame(
            {
                "case_id": ["case1", "case2"],
                "activity": ["activity1", "activity2"],
                "timestamp": ["2025-01-01", "2025-01-02"],
            }
        )
        csv_data = self.exporter.export_to_csv_data(df, ",")
        self.assertIsInstance(csv_data, str)
        self.assertIn("case_id,activity,timestamp", csv_data)
        self.assertIn("case1,activity1,2025-01-01", csv_data)
        self.assertIn("case2,activity2,2025-01-02", csv_data)

    def test_export_xes_to_bytes(self):
        """Test that XES ElementTree is exported to bytes."""
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
        xes_tree = ET.ElementTree(root)

        with tempfile.TemporaryDirectory() as temp_dir:
            st.session_state.session_tmp_dir = temp_dir
            xes_bytes = self.exporter.export_to_xes_bytes(xes_tree)

        self.assertIsInstance(xes_bytes, bytes)
        self.assertIn(b"<log", xes_bytes)
        self.assertIn(b"<trace>", xes_bytes)
        self.assertIn(b"<event>", xes_bytes)


if __name__ == "__main__":
    unittest.main()
