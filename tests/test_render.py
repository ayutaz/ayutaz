from __future__ import annotations

import unittest
import xml.etree.ElementTree as ET

from profile_stats.model import LanguageStat, Report, Stats
from profile_stats.render import render_languages_svg, render_stats_svg


class RenderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.report = Report(
            username="ayutaz",
            stats=Stats(3, 1200, 25, 42, 2, 2_500_000),
            languages=(
                LanguageStat("Python & tools", "#3572A5", 2_000_000, 80.0),
                LanguageStat("C#", "#178600", 500_000, 20.0),
            ),
            fetched_repositories=4,
            excluded_counts={"archived": 1, "private": 0, "fork": 0, "named": 0},
        )

    def test_stats_svg_is_valid_xml_and_escapes_title(self) -> None:
        svg = render_stats_svg(self.report, "Yousan <Stats> & more")

        root = ET.fromstring(svg)
        self.assertTrue(root.tag.endswith("svg"))
        self.assertIn("Yousan &lt;Stats&gt; &amp; more", svg)
        self.assertNotIn("<Stats>", svg)

    def test_languages_svg_uses_percentages_and_escapes_names(self) -> None:
        svg = render_languages_svg(self.report, "Top Languages")

        ET.fromstring(svg)
        self.assertIn("80.0%", svg)
        self.assertIn("Python &amp; tools", svg)


if __name__ == "__main__":
    unittest.main()
