"""The docs lane: repository-relative Markdown links resolve.

The finding this closes: a fresh clone shipped twelve links straight at
`research/program/brief.md` and `research/program/portfolio.yaml`, which are correctly
absent until their gates open. The links were wrong; the absent files were not.

    python3 -m unittest discover -s scripts/tests -p 'test_*.py'
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checks import docs  # noqa: E402
from fixtures import CheckerFixture  # noqa: E402


class DocsTests(CheckerFixture):
    def write(self, relative: str, text: str) -> None:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def links(self) -> list[str]:
        errors: list[str] = []
        docs.check(self.root, errors)
        return errors

    def test_a_link_to_a_gated_file_that_is_absent_is_an_error(self):
        """The exact defect: a navigation table pointing at an optional plane."""
        self.write("README.md", "See [the brief](research/program/brief.md).\n")

        self.assertIn("link 'research/program/brief.md' does not resolve", self.links()[0])

    def test_a_link_that_resolves_is_accepted(self):
        self.write("README.md", "See [the schema](docs/schema.md).\n")
        self.write("docs/schema.md", "content\n")

        self.assertEqual(self.links(), [])

    def test_external_links_and_fragments_are_left_alone(self):
        self.write("README.md",
                   "[site](https://example.invalid/x) [top](#heading) "
                   "[mail](mailto:someone@example.invalid) "
                   "[anchored](docs/schema.md#a-section)\n")
        self.write("docs/schema.md", "content\n")

        self.assertEqual(self.links(), [])

    def test_append_only_archives_are_exempt(self):
        """decisions/ and research/reviews/ deliberately name paths that have moved.

        Rewriting them to satisfy a link checker is the rewriting constraint 7 forbids.
        """
        self.write("decisions/2026-01-01-a.md", "[gone](old/path.md)\n")
        self.write("research/reviews/2026-01-01-b.md", "[gone](old/path.md)\n")

        self.assertEqual(self.links(), [])

    def test_scaffolds_are_exempt_because_their_links_point_at_the_destination(self):
        self.write("templates/brief.md", "[the ledger](ledger.yaml)\n")

        self.assertEqual(self.links(), [])

    def test_an_absolute_link_is_rejected_by_name(self):
        self.write("README.md", "[bad](/research/program/ledger.yaml)\n")

        self.assertIn("is absolute", self.links()[0])


if __name__ == "__main__":
    unittest.main()
