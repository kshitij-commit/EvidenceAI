import unittest

import pandas as pd

from src.data import audit_dataset


class DatasetAuditTests(unittest.TestCase):
    def test_reports_row_counts_missingness_and_link_integrity(self):
        tables = {
            "main": pd.DataFrame({"_link": ["a", "b", "b"], "ocid": ["x", "y", "z"]}),
            "awards": pd.DataFrame({"_link": ["award-1"], "_link_main": ["a"]}),
            "awards_suppliers": pd.DataFrame({"_link_main": ["a", "missing"], "_link_awards": ["award-1", "bad"]}),
        }

        result = audit_dataset(tables)

        self.assertEqual(result["main_link_rows"], 3)
        self.assertEqual(result["main_link_unique"], 2)
        self.assertEqual(result["files"]["awards_suppliers"]["link_main_matched_to_main"], 1)
        self.assertEqual(result["files"]["awards_suppliers"]["link_main_unmatched"], 1)
        self.assertEqual(result["supplier_award_links_matched"], 1)

    def test_requires_main_link(self):
        with self.assertRaises(ValueError):
            audit_dataset({"main": pd.DataFrame({"id": [1]})})


if __name__ == "__main__":
    unittest.main()
