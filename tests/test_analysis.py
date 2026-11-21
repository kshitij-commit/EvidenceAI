import unittest

import pandas as pd

from src.analysis import investigation_flags, tender_records


class AnalysisTests(unittest.TestCase):
    def test_tender_award_supplier_links_are_exact(self):
        tables = {
            "main": pd.DataFrame({"_link": ["0.10"], "id": ["tender-1"], "award_date": [None], "tender_datePublished": [None]}),
            "awards": pd.DataFrame({"_link": ["award-1"], "_link_main": ["0.10"], "value_amount": [100.0], "value_currency": ["INR"]}),
            "awards_suppliers": pd.DataFrame({"_link_awards": ["award-1"], "name": ["Supplier A"]}),
        }
        result = tender_records(tables)
        self.assertEqual(len(result), 1)
        self.assertEqual(result.loc[0, "award_count"], 1)
        self.assertEqual(result.loc[0, "supplier_names"], "Supplier A")

    def test_missing_currency_is_quality_note_not_priority_score(self):
        records = pd.DataFrame({
            "tender_value_amount": [1000.0], "tender_value_currency": [None],
            "tender_numberOfTenderers": [3], "tender_tenderPeriod_durationInDays": [10],
        })
        result = investigation_flags(records)
        self.assertTrue(result.loc[0, "flag_missing_amount_or_currency"])
        self.assertEqual(result.loc[0, "investigation_score"], 0)


if __name__ == "__main__":
    unittest.main()
