import unittest

from pyairbnb import standardize


def details_meta(sections, amenities=None):
    meta = {
        "data": {
            "presentation": {
                "stayProductDetailPage": {
                    "sections": {
                        "metadata": {
                            "loggingContext": {
                                "eventDataLogging": {
                                    "listingLat": 1.0,
                                    "listingLng": 2.0,
                                    "roomType": "Entire home",
                                    "visibleReviewCount": 10,
                                }
                            },
                            "seoFeatures": {"title": "Sunny Flat - great location"},
                            "sharingConfig": {"title": "Sunny Flat in Barranco"},
                        },
                        "sections": sections,
                    }
                }
            }
        }
    }
    if amenities is not None:
        meta["data"]["node"] = {"pdpPresentation": {"amenities": amenities}}
    return meta


class FromDetailsFallbackTests(unittest.TestCase):
    def test_title_falls_back_to_seo_features_when_section_missing(self):
        data = standardize.from_details(details_meta([]))
        self.assertEqual(data["title"], "Sunny Flat")
        self.assertEqual(data["sub_description"]["title"], "Sunny Flat in Barranco")

    def test_primary_title_section_wins_over_fallback(self):
        meta = details_meta(
            [{"title": "Primary Title", "section": {"__typename": "PdpTitleSection"}}]
        )
        data = standardize.from_details(meta)
        self.assertEqual(data["title"], "Primary Title")

    def test_description_falls_back_to_description_modal(self):
        meta = details_meta(
            [
                {
                    "sectionId": "DESCRIPTION_MODAL",
                    "section": {
                        "items": [
                            {"title": "The space", "html": {"htmlText": "<p>Bright flat</p>"}},
                            {"html": {"htmlText": "No header text"}},
                        ]
                    },
                }
            ]
        )
        data = standardize.from_details(meta)
        self.assertEqual(
            data["description"],
            "The space: <p>Bright flat</p>\n\nNo header text",
        )

    def test_amenities_fall_back_to_preview_groups(self):
        meta = details_meta(
            [{"section": {"__typename": "AmenitiesSection"}}],
            amenities={
                "previewAmenitiesGroups": [
                    {
                        "title": "What this place offers",
                        "amenities": [
                            {
                                "title": "Wifi",
                                "subtitle": {"text": "Fast"},
                                "icon": "wifi",
                                "available": True,
                            }
                        ],
                    }
                ]
            },
        )
        data = standardize.from_details(meta)
        self.assertEqual(data["amenities"][0]["values"][0]["title"], "Wifi")
        self.assertEqual(data["amenities"][0]["values"][0]["available"], True)

    def test_amenities_see_all_groups_take_priority_over_preview(self):
        meta = details_meta(
            [{"section": {"__typename": "AmenitiesSection"}}],
            amenities={
                "seeAllAmenitiesGroups": [
                    {
                        "title": "What this place offers",
                        "amenities": [{"title": "Pool", "available": True}],
                    }
                ],
                "previewAmenitiesGroups": [
                    {
                        "title": "What this place offers",
                        "amenities": [{"title": "Wifi", "available": True}],
                    }
                ],
            },
        )
        data = standardize.from_details(meta)
        self.assertEqual(data["amenities"][0]["values"][0]["title"], "Pool")

    def test_not_included_amenity_group_marks_unavailable(self):
        for group_title in ("Not included", "What this place doesn't include"):
            with self.subTest(group_title=group_title):
                meta = details_meta(
                    [{"section": {"__typename": "AmenitiesSection"}}],
                    amenities={
                        "seeAllAmenitiesGroups": [
                            {
                                "title": group_title,
                                "amenities": [{"title": "Dryer", "icon": "dryer"}],
                            }
                        ]
                    },
                )
                data = standardize.from_details(meta)
                self.assertEqual(data["amenities"][0]["values"][0]["available"], False)


if __name__ == "__main__":
    unittest.main()
