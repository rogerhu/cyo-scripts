import unittest
from unittest.mock import MagicMock, patch
import pandas as pd

from transform_file import transform_excel_to_csv, split_name, process_parents, combine_address, format_dob


class TestExcelToCsvTransformer(unittest.TestCase):

    # -------------------------------------------------------------------------
    # Tests for split_name()
    # -------------------------------------------------------------------------
    def test_split_name_comma_format(self):
        """Tests parsing 'Last, First' standard string."""
        first, last = split_name("Smith, John")
        self.assertEqual(first, "John")
        self.assertEqual(last, "Smith")

    def test_split_name_space_fallback(self):
        """Tests fallback when no comma is present ('First Last')."""
        first, last = split_name("John Smith")
        self.assertEqual(first, "John")
        self.assertEqual(last, "Smith")

    def test_split_name_single_word(self):
        """Tests single word input."""
        first, last = split_name("Madonna")
        self.assertEqual(first, "Madonna")
        self.assertEqual(last, "")

    def test_split_name_empty_or_null(self):
        """Tests NaN and empty string handling."""
        self.assertEqual(split_name(""), ("", ""))
        self.assertEqual(split_name(None), ("", ""))
        self.assertEqual(split_name(pd.NA), ("", ""))

    # -------------------------------------------------------------------------
    # Tests for combine_address()
    # -------------------------------------------------------------------------
    def test_combine_address_both_lines(self):
        """Combines Line 1 and Line 2 with comma separation."""
        result = combine_address("123 Main St", "Apt 4B")
        self.assertEqual(result, "123 Main St, Apt 4B")

    def test_combine_address_line1_only(self):
        """Handles missing Line 2 gracefully."""
        result = combine_address("123 Main St", None)
        self.assertEqual(result, "123 Main St")

    def test_combine_address_empty(self):
        """Handles empty values."""
        self.assertEqual(combine_address(None, None), "")

    # -------------------------------------------------------------------------
    # Tests for process_parents()
    # -------------------------------------------------------------------------
    def test_process_parents_parent1_matches_registration(self):
        """Default order kept when Registration Email matches Parent 1."""
        row = pd.Series(
            {
                "Registration Email": "parent1@test.com",
                "Parent 1 Name": "Doe, Jane",
                "Parent 1 Email": "parent1@test.com",
                "Parent 1 Cell": "555-0101",
                "Parent 2 Name": "Doe, John",
                "Parent 2 Email": "parent2@test.com",
                "Parent 2 Cell": "555-0102",
            }
        )
        row.name = 0
        res = process_parents(row)

        self.assertEqual(res["p1fn"], "Jane")
        self.assertEqual(res["p1email"], "parent1@test.com")
        self.assertEqual(res["p2fn"], "John")
        self.assertEqual(res["p2email"], "parent2@test.com")

    def test_process_parents_parent2_matches_registration_swaps(self):
        """Swaps Parent 1 and Parent 2 when Registration Email matches Parent 2."""
        row = pd.Series(
            {
                "Registration Email": "parent2@test.com",
                "Parent 1 Name": "Doe, Jane",
                "Parent 1 Email": "parent1@test.com",
                "Parent 1 Cell": "555-0101",
                "Parent 2 Name": "Doe, John",
                "Parent 2 Email": "parent2@test.com",
                "Parent 2 Cell": "555-0102",
            }
        )
        row.name = 1
        res = process_parents(row)

        # Parent 2 becomes p1
        self.assertEqual(res["p1fn"], "John")
        self.assertEqual(res["p1email"], "parent2@test.com")
        # Parent 1 becomes p2
        self.assertEqual(res["p2fn"], "Jane")
        self.assertEqual(res["p2email"], "parent1@test.com")

    def test_process_parents_mismatch_raises_value_error(self):
        """Raises ValueError when Registration Email matches neither parent."""
        row = pd.Series(
            {
                "Registration Email": "unknown@test.com",
                "Parent 1 Name": "Doe, Jane",
                "Parent 1 Email": "parent1@test.com",
                "Parent 1 Cell": "",
                "Parent 2 Name": "",
                "Parent 2 Email": "",
                "Parent 2 Cell": "",
            }
        )
        row.name = 2

        with self.assertRaises(ValueError) as ctx:
            process_parents(row)

        self.assertIn("Row 2: Registration Email 'unknown@test.com'", str(ctx.exception))

    # -------------------------------------------------------------------------
    # Integration test for transform_excel_to_csv()
    # -------------------------------------------------------------------------
    @patch("pandas.read_excel")
    @patch("pandas.DataFrame.to_csv")
    def test_transform_excel_to_csv_end_to_end(self, mock_to_csv, mock_read_excel):
        """Tests end-to-end transformation mock pipeline."""
        mock_input = pd.DataFrame(
            [
                {
                    "Athlete Name": "Runner, Alex",
                    "Address Line 1": "100 Track Way",
                    "Address Line 2": "",
                    "City": "Springfield",
                    "State": "IL",
                    "ZIP": "62701",
                    "DOB": "2010-05-15",
                    "Registration Email": "mom@test.com",
                    "Team": "Eagles",
                    "Division": "U12",
                    "Parent 1 Name": "Runner, Mom",
                    "Parent 1 Email": "mom@test.com",
                    "Parent 1 Cell": "555-9999",
                    "Parent 2 Name": "",
                    "Parent 2 Email": "",
                    "Parent 2 Cell": "",
                }
            ]
        )
        mock_read_excel.return_value = mock_input

        # Execute function
        transform_excel_to_csv("input.xlsx", "output.csv")

        # Verify output saved to CSV path
        mock_to_csv.assert_called_once_with("output.csv", index=False)

    def test_format_dob_variations(self):
        # m/dd/yy
        self.assertEqual(format_dob("1/05/12"), "01/05/2012")
        # mm/dd/yy
        self.assertEqual(format_dob("01/05/12"), "01/05/2012")
        # m/d/yyyy
        self.assertEqual(format_dob("1/5/2012"), "01/05/2012")
        # Empty / NaN
        self.assertEqual(format_dob(None), "")
        self.assertEqual(format_dob(""), "")

    def test_format_phone(self):
        self.assertEqual(format_phone("5551234567.0"), "5551234567")
        self.assertEqual(format_phone(5551234567.0), "5551234567")
        self.assertEqual(format_phone("555-123-4567"), "555-123-4567")
        self.assertEqual(format_phone(None), "")

if __name__ == "__main__":
    unittest.main()
