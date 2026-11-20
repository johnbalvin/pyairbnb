import unittest
from unittest.mock import MagicMock, patch

from pyairbnb import api


def response(text: str) -> MagicMock:
    result = MagicMock()
    result.text = text
    result.raise_for_status.return_value = None
    return result


class ApiGetTests(unittest.TestCase):
    @patch("pyairbnb.api.requests.get")
    def test_returns_parsed_key_from_homepage(self, get):
        get.return_value = response('script: "api_config":{"key":"abc123"}')

        self.assertEqual(api.get(""), "abc123")

    @patch("pyairbnb.api.requests.get")
    def test_falls_back_to_public_key_when_homepage_is_unparseable(self, get):
        get.return_value = response("<html>landing page without api_config</html>")

        self.assertEqual(api.get(""), api.FALLBACK_API_KEY)

    @patch("pyairbnb.api.requests.post")
    @patch("pyairbnb.api.requests.get")
    def test_falls_back_after_failed_handoff(self, get, post):
        get.return_value = response(
            '<form action="https://www.airbnb.ca/geo/handoff">'
            '<input name="payload" value="abc">'
        )
        post.return_value = response("<html>still no api_config</html>")

        self.assertEqual(api.get(""), api.FALLBACK_API_KEY)
        post.assert_called_once()

    @patch("pyairbnb.api.requests.get")
    def test_unparseable_without_handoff_is_single_request(self, get):
        get.return_value = response("<html>unparseable</html>")

        self.assertEqual(api.get(""), api.FALLBACK_API_KEY)
        get.assert_called_once()


if __name__ == "__main__":
    unittest.main()
