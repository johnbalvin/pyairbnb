import unittest
import warnings
from unittest.mock import patch

import pyairbnb


def search_page(results, page_count=1):
    return {
        "results": results,
        "data": {
            "presentation": {
                "staysSearch": {
                    "results": {
                        "paginationInfo": {
                            "pageCursors": [f"page-{index}" for index in range(page_count)]
                        }
                    }
                }
            }
        },
    }


class SearchCompletenessTests(unittest.TestCase):
    @patch("pyairbnb.start.standardize.from_search", side_effect=lambda raw: raw["results"])
    @patch("pyairbnb.start.api.get", return_value="key")
    def test_capped_search_emits_a_truncation_warning(self, _, __):
        pages = [
            search_page([{"room_id": str(index)}], page_count=7)
            for index in range(7)
        ]

        with (
            patch("pyairbnb.start.search.get", side_effect=pages),
            warnings.catch_warnings(record=True) as caught,
        ):
            warnings.simplefilter("always")
            results = pyairbnb.search_all("", "", 1, 1, 0, 0, 10)

        self.assertEqual(len(results), 7)
        self.assertEqual(len(caught), 1)
        self.assertIsInstance(
            caught[0].message, pyairbnb.SearchResultsTruncatedWarning
        )

    @patch("pyairbnb.start.standardize.from_search", side_effect=lambda raw: raw["results"])
    @patch("pyairbnb.start.api.get", return_value="key")
    def test_complete_search_subdivides_capped_bounds(self, _, __):
        def fake_search(**kwargs):
            bounds = (
                kwargs["sw_lat"],
                kwargs["sw_long"],
                kwargs["ne_lat"],
                kwargs["ne_long"],
            )
            full_bounds = (0, 0, 1, 1)
            tiles = {
                (0, 0, 0.5, 0.5): "south-west",
                (0, 0.5, 0.5, 1): "south-east",
                (0.5, 0, 1, 0.5): "north-west",
                (0.5, 0.5, 1, 1): "north-east",
            }
            if bounds == full_bounds:
                return search_page([{"room_id": "parent"}], page_count=2)
            return search_page([{"room_id": tiles[bounds]}], page_count=1)

        with patch("pyairbnb.start.search.get", side_effect=fake_search) as get:
            results = pyairbnb.search_all_complete("", "", 1, 1, 0, 0, 10)

        self.assertEqual(
            results,
            [
                {"room_id": "parent"},
                {"room_id": "south-west"},
                {"room_id": "south-east"},
                {"room_id": "north-west"},
                {"room_id": "north-east"},
            ],
        )
        self.assertEqual(get.call_count, 5)

    @patch("pyairbnb.start._search_single_page_bbox")
    @patch("pyairbnb.start.api.get", return_value="key")
    def test_complete_search_reports_partial_results_when_budget_is_exhausted(
        self, _, search_single_page
    ):
        search_single_page.return_value = ([{"room_id": "parent"}], 2)

        with self.assertRaises(pyairbnb.SearchCoverageError) as caught:
            pyairbnb.search_all(
                "",
                "",
                1,
                1,
                0,
                0,
                10,
                complete=True,
                max_requests=1,
            )

        self.assertEqual(caught.exception.results, [{"room_id": "parent"}])
        search_single_page.assert_called_once()


if __name__ == "__main__":
    unittest.main()
