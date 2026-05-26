import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

import pandas as pd
import pm4py

from app.converters.csv_to_xes_converter import CsvToXesConverter
from app.io_operations.import_operations import ImportOperations


class CsvToXesConversionTest(unittest.TestCase):
    def setUp(self):
        """Set up before running tests."""
        self.csv_to_xes_converter = CsvToXesConverter()
        self.test_csv_dir = os.path.join(os.path.dirname(__file__), "..", "testcsv")
        self.sample_csv_path = os.path.join(self.test_csv_dir, "genetic_test.csv")

    def test_csv_to_xes_conversion_returns_element_tree(self):
        """Test that CSV to XES conversion returns ElementTree."""
        with open(self.sample_csv_path, "r", encoding="utf-8") as csv_file:
            df = pd.read_csv(csv_file, delimiter=",")

        xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
            df,
            case_id_col="Case ID",
            activity_col="Activity",
            timestamp_col="Timestamp",
        )

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertIsInstance(summary, dict)
        self.assertIsInstance(dropped_rows, int)

    def test_csv_to_xes_conversion(self):
        """Test the CSV to XES conversion."""
        with open(self.sample_csv_path, "r", encoding="utf-8") as csv_file:
            df = pd.read_csv(csv_file, delimiter=",")

        xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
            df,
            case_id_col="Case ID",
            activity_col="Activity",
            timestamp_col="Timestamp",
        )

        attributes = self._get_unique_attribute_keys(xes_tree)
        ids = self._get_trace_case_ids(xes_tree)

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertIsNotNone(xes_tree.getroot())
        self.assertSetEqual(set(ids), {"1", "2", "3", "4"})
        self.assertSetEqual(
            set(attributes), {"concept:name", "time:timestamp", "Person"}
        )

    def test_csv_to_xes_preserves_existing_concept_name(self):
        """Test CSV to XES conversion using a sample an existing 'concept:name' column, where user selects
        another column as activity column, the original column is renamed and columns are not merged
        together.
        """
        csv_path = os.path.join(self.test_csv_dir, "existing_concept_name.csv")
        with open(csv_path, "r", encoding="utf-8") as csv_file:
            df = pd.read_csv(csv_file, delimiter=",")

        xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
            df,
            case_id_col="case:concept:name",
            activity_col="lifecycle:transition",
            timestamp_col="time:timestamp",
        )

        concept_names = self._get_event_attribute_values(xes_tree, "concept:name")
        original_concept_names = self._get_event_attribute_values(
            xes_tree, "original:concept:name"
        )
        concept_name_counts = self._count_event_attributes(xes_tree, "concept:name")

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertIsNotNone(xes_tree.getroot())
        self.assertTrue(all(count == 1 for count in concept_name_counts))
        self.assertEqual(
            concept_names,
            ["Awaiting Assignment", "In Progress", "Assigned", "In Progress", "Closed"],
        )
        self.assertEqual(
            original_concept_names,
            ["Queued", "Accepted", "Accepted", "Accepted", "Completed"],
        )

    def test_csv_to_xes_conversion_parses_genetic_timestamp_format(self):
        """Test that CSV to XES conversion accepts %d-%m-%Y:%H.%M format."""
        test_df = pd.DataFrame(
            {
                "case:concept:name": ["case1", "case1", "case2", "case2"],
                "concept:name": ["activity1", "activity2", "activity1", "activity3"],
                "time:timestamp": [
                    "02-05-2025:12.11",
                    "03-05-2025:12.15",
                    "04-05-2025:12.17",
                    "04-05-2025:13.25",
                ],
            }
        )

        xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
            test_df,
            case_id_col="case:concept:name",
            activity_col="concept:name",
            timestamp_col="time:timestamp",
        )
        attributes = self._get_unique_attribute_keys(xes_tree)

        self.assertIsInstance(xes_tree, ET.ElementTree)
        self.assertIsNotNone(xes_tree.getroot())
        self.assertIn("time:timestamp", attributes)

    def test_csv_to_xes_conversion_rejects_invalid_timestamp_format(self):
        """Test that CSV to XES conversion fails for unknown timestamp format."""
        invalid_df = pd.DataFrame(
            {
                "case:concept:name": ["case1", "case1", "case2", "case2"],
                "concept:name": ["activity1", "activity2", "activity1", "activity3"],
                "time:timestamp": [
                    "12-02-2027-59:00",
                    "13-02-2029-42:00",
                    "17-02-2029-42:00",
                    "130-02-2029-42:00",
                ],
            }
        )
        with self.assertRaises(ValueError) as context:
            self.csv_to_xes_converter.convert(
                invalid_df,
                case_id_col="case:concept:name",
                activity_col="concept:name",
                timestamp_col="time:timestamp",
            )

        self.assertEqual(str(context.exception), "The timestamp format is unknown.")

    def test_csv_to_xes_conversion_rejects_duplicate_selected_columns(self):
        """Test that CSV to XES conversion rejects when two duplicate columns were selected."""
        df = pd.DataFrame(
            {
                "Case ID": ["case1"],
                "Activity": ["activity1"],
                "Timestamp": ["29.3.10 9:28"],
            }
        )

        with self.assertRaises(ValueError) as context:
            self.csv_to_xes_converter.convert(
                df,
                case_id_col="Case ID",
                activity_col="Activity",
                timestamp_col="Case ID",
            )
        self.assertIn("Please select three different columns", str(context.exception))

    def test_csv_to_xes_conversion_compare_to_pm4py_conversion(self):
        """Test CSV to XES conversion correctness comparing to pm4py library conversion."""
        csv_path = os.path.join(self.test_csv_dir, "test_csv.csv")
        with open(csv_path, "r", encoding="utf-8") as csv_file:
            df = pd.read_csv(csv_file, delimiter=",")

        xes_tree, summary, dropped_rows = self.csv_to_xes_converter.convert(
            df,
            case_id_col="case",
            activity_col="event",
            timestamp_col="timestamp",
        )

        pm4py_xes_tree = self._convert_using_pm4py(df)

        self.assertEqual(
            self._get_trace_case_ids(xes_tree),
            self._get_trace_case_ids(pm4py_xes_tree),
        )
        self.assertEqual(
            self._get_event_attribute_values(xes_tree, "concept:name"),
            self._get_event_attribute_values(pm4py_xes_tree, "concept:name"),
        )
        self.assertEqual(
            self._get_formatted_timestamps(xes_tree),
            self._get_formatted_timestamps(pm4py_xes_tree),
        )
        self.assertEqual(
            self._count_events(xes_tree), self._count_events(pm4py_xes_tree)
        )

    def _convert_using_pm4py(self, df: pd.DataFrame) -> ET.ElementTree:
        """Convert Dataframe to XES event log using pm4py library.

        Parameters
        ----------
        df : pd.DataFrame
            The parsed dataframe.

        Returns
        -------
        ET.ElementTree
            The converted XES element tree.
        """
        pm4py_df = pm4py.format_dataframe(
            df,
            case_id="case",
            activity_key="event",
            timestamp_key="timestamp",
        )
        event_log = pm4py.convert_to_event_log(pm4py_df)

        with tempfile.TemporaryDirectory() as temp_dir:
            pm4py_xes_path = os.path.join(temp_dir, "exported.xes")
            pm4py.write_xes(event_log, pm4py_xes_path)
            import_model = ImportOperations()
            pm4py_xes_tree = import_model.read_xes(pm4py_xes_path)

            return pm4py_xes_tree

    def _get_formatted_timestamps(self, xes_tree: ET.ElementTree) -> list[str]:
        """Return formatted timestamp values from element tree.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            Parsed ElementTree.

        Returns
        -------
        list[str]
            Normalized timestamp values.
        """
        timestmaps = self._get_event_attribute_values(xes_tree, "time:timestamp")

        return [
            pd.to_datetime(timestamp, utc=True).isoformat() for timestamp in timestmaps
        ]

    def _count_events(self, xes_tree: ET.ElementTree) -> int:
        """Count all events in XES tree.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            The parsed element tree.

        Returns
        -------
        int
            Number of event elements.
        """
        root = xes_tree.getroot()
        event_count = 0
        for elem in root.iter():
            if elem.tag.endswith("event"):
                event_count += 1

        return event_count

    def _get_trace_case_ids(self, xes_tree: ET.ElementTree) -> list[str]:
        """Get case IDs from trace-level concept:name attributes.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            The parsed tree.

        Returns
        -------
        list[str]
            Returned case IDs.
        """
        root = xes_tree.getroot()
        case_ids = []

        for trace in root.iter():
            if not trace.tag.endswith("trace"):
                continue
            for child in trace:
                if child.get("key") == "concept:name":
                    case_ids.append(child.get("value"))
        return case_ids

    def _get_unique_attribute_keys(self, xes_tree: ET.ElementTree) -> list[str]:
        """Get XES unique attribute keys from an ElementTree.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            The parsed ElementTree.

        Returns
        -------
        list[str]
            A list of attribute keys extracted from xes_tree.
        """
        root = xes_tree.getroot()
        attributes = []
        for elem in root.iter():
            if elem.get("key") is not None:
                if elem.get("key") not in attributes:
                    attributes.append(elem.get("key"))

        return attributes

    def _get_event_attribute_values(
        self, xes_tree: ET.ElementTree, attribute_key: str
    ) -> list[str]:
        """Get values of a specific event attribute from an XES tree.

        Parameters
        ----------
        xes_tree : ET.ElementTree
            Parsed ElementTree.
        attribute_key : str
            The attribute which values will be returned.

        Returns
        -------
        list[str]
            Returned values of selected attribute.
        """
        root = xes_tree.getroot()
        values = []

        for event in root.iter():
            if not event.tag.endswith("event"):
                continue

            for child in event:
                if child.get("key") == attribute_key:
                    values.append(child.get("value"))

        return values

    def _count_event_attributes(
        self, xes_tree: ET.ElementTree, attribute_key: str
    ) -> list[int]:
        """Count how often an attribute appears in each event."""
        root = xes_tree.getroot()
        counts = []

        for event in root.iter():
            if not event.tag.endswith("event"):
                continue

            count = sum(1 for child in event if child.get("key") == attribute_key)
            counts.append(count)

        return counts


if __name__ == "__main__":
    unittest.main()
