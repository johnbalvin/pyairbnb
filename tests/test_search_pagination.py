import unittest
from unittest.mock import patch

import pyairbnb


def page(results, **pagination):
    """A fake StaysSearch response; `standardize.from_search` is patched to read `results` off it."""
    return {"results": results, "data": {"presentation": {"staysSearch": {"results": {"paginationInfo": pagination}}}}}


@patch("pyairbnb.start.standardize.from_search", side_effect=lambda raw: raw["results"])
@patch("pyairbnb.start.api.get", return_value="key")
class SearchPaginationTests(unittest.TestCase):
    def run_both(self, pages):
        """Runs search_all and search_all_from_url over the same pages; returns (results, cursors asked for) of each."""
        out = []
        for call in (
            lambda: pyairbnb.search_all("", "", 1, 1, 0, 0, 10, 0, 0),
            lambda: pyairbnb.search_all_from_url("https://www.airbnb.com/s/x/homes?ne_lat=1"),
        ):
            with patch("pyairbnb.start.search.get", side_effect=list(pages)) as get:
                results = call()
            out.append((results, [c.kwargs.get("cursor", c.args[1] if len(c.args) > 1 else None) for c in get.call_args_list]))
        return out

    def test_follows_next_page_cursor(self, *_):
        pages = [page([1, 2], nextPageCursor="b"), page([3], nextPageCursor=None)]
        for results, cursors in self.run_both(pages):
            self.assertEqual(results, [1, 2, 3])
            self.assertEqual(cursors, ["", "b"])

    def test_follows_page_cursors_listed_up_front(self, *_):
        cursors_up_front = {"pageCursors": ["a", "b", "c"]}
        pages = [page([1], **cursors_up_front), page([2], **cursors_up_front), page([3], **cursors_up_front)]
        for results, cursors in self.run_both(pages):
            self.assertEqual(results, [1, 2, 3])
            self.assertEqual(cursors, ["", "b", "c"])

    def test_single_page_makes_one_request(self, *_):
        for results, cursors in self.run_both([page([1], pageCursors=["a"])]):
            self.assertEqual(results, [1])
            self.assertEqual(cursors, [""])

    def test_a_repeated_cursor_does_not_loop(self, *_):
        pages = [page([1], nextPageCursor="b"), page([2], nextPageCursor="b")]
        for results, cursors in self.run_both(pages):
            self.assertEqual(results, [1, 2])
            self.assertEqual(cursors, ["", "b"])

    def test_empty_page_stops(self, *_):
        for results, cursors in self.run_both([page([], pageCursors=["a", "b"])]):
            self.assertEqual(results, [])
            self.assertEqual(cursors, [""])


if __name__ == "__main__":
    unittest.main()
