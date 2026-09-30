"""The manuscript reader: MyST's tree turned into anchors, and what it refuses.

One real MyST project is built once for the whole class, holding every case at the same
time — a MyST build is the slow part, and these assertions only read its result. The rules
that consume the anchors are tested in ``test_ledger.py`` without a build.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from checks import manuscript  # noqa: E402
from fixtures import write_myst_project  # noqa: E402

MODULE = """\
% :::{prf:lemma}
% :label: lem:commented
% A claim parked behind a comment is not a claim.
% :::

(sec:orientation)=
## Orientation

:::{prf:lemma}
:label: lem:anchored
A statement with its own numbered display, which stays structural:

```{math}
:label: eq:inner
x = x
```
:::

::::{prf:proposition}
:label: prop:nested
A statement.

:::{prf:proof}
- a proof nested in its claim carries no label of its own
:::
::::

:::{table} A table inside the manuscript
:label: tab:inner
| a | b |
|---|---|
| 1 | 2 |
:::

:::{prf:remark}
:label: rem:aside
An expository remark is structural.
:::

:::{prf:question}
:label: q:unknown
Not a directive MyST knows.
:::

See [](#nope:missing) and {prf:ref}`prf:missing`.
"""

SECOND = """\
# Second

:::{prf:lemma}
:label: lem:anchored
The same label again.
:::

:::{prf:lemma}
:label: a:b-c
One anchor.
:::

:::{prf:lemma}
:label: a-b:c
The same anchor.
:::

:::{prf:corollary}
:label: cor:bodiless
:::

:::{prf:lemma}
:label: lem:twin-a
For all $x \\ge 0$, see [](#prop:nested):
$x^2 \\ge 0$.
:::

::::{prf:lemma} 
:label: lem:twin-b
For all   $x \\ge 0$, see [](#prop:nested): $x^2 \\ge 0$.

:::{prf:proof}
Obvious.
:::
::::

:::{prf:lemma}
:label: lem:edited
For all $x \\ge 0$, see [](#prop:nested):
$x^3 \\ge 0$.
:::

:::{prf:proposition}
:label: prop:twin
For all $x \\ge 0$, see [](#prop:nested):
$x^2 \\ge 0$.
:::
"""

DOSSIER = """\
---
title: A dossier
ledger-node: prop:nested
---

:::{prf:theorem}
:label: thm:sol-nested
Restated in the dossier; see [](#prop:nested).
:::
"""


class ManuscriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tempdir = tempfile.TemporaryDirectory()
        root = Path(cls.tempdir.name)
        write_myst_project(root)
        (root / "modules").mkdir()
        (root / "modules/00-first.md").write_text(MODULE)
        (root / "modules/01-second.md").write_text(SECOND)
        (root / "solutions").mkdir()
        (root / "solutions/prop-nested.md").write_text(DOSSIER)
        cls.errors: list[str] = []
        cls.labels = manuscript.manuscript_labels(root, cls.errors)
        cls.text = "\n".join(cls.errors)

    @classmethod
    def tearDownClass(cls):
        cls.tempdir.cleanup()

    def test_a_claim_directive_label_is_a_claim_of_that_kind(self):
        self.assertEqual({k: v for k, v in self.labels["lem:anchored"].items()
                          if k != "fingerprint"},
                         {"kind": "lemma", "file": "modules/00-first.md"})
        self.assertNotIn("fingerprint", self.labels["sec:orientation"])
        self.assertEqual(self.labels["prop:nested"]["kind"], "proposition")

    def test_headings_equations_tables_and_remarks_are_structural(self):
        for label in ("sec:orientation", "eq:inner", "tab:inner", "rem:aside"):
            with self.subTest(label=label):
                self.assertIsNone(self.labels[label]["kind"])

    def test_a_commented_out_claim_is_not_a_label(self):
        self.assertNotIn("lem:commented", self.labels)

    def test_a_heading_without_a_label_contributes_no_anchor(self):
        self.assertNotIn("Orientation", self.labels)
        self.assertNotIn("Second", self.labels)

    def test_a_label_outside_modules_is_not_a_manuscript_anchor(self):
        self.assertNotIn("thm:sol-nested", self.labels)

    def test_an_unknown_directive_is_an_error_not_a_silent_paragraph(self):
        self.assertIn("modules/00-first.md:", self.text)
        self.assertIn("unknown MyST directive 'prf:question'", self.text)
        self.assertNotIn("q:unknown", self.labels)

    def test_an_unresolved_cross_reference_is_an_error(self):
        self.assertIn("cross-reference to 'nope:missing' does not resolve", self.text)
        self.assertIn("cross-reference to 'prf:missing' does not resolve", self.text)

    def test_a_resolved_cross_reference_from_a_dossier_is_fine(self):
        self.assertNotIn("prop:nested' does not resolve", self.text)

    def test_one_label_lives_in_one_place(self):
        self.assertIn("duplicate label 'lem:anchored'", self.text)

    def test_a_fingerprint_ignores_layout_and_catches_an_edit(self):
        """Wrapping, spacing, numbering, a reference's rendered text and a nested proof
        leave the statement as it was; a changed symbol or word does not."""
        fingerprint = self.labels["lem:twin-a"]["fingerprint"]
        self.assertEqual(self.labels["lem:twin-b"]["fingerprint"], fingerprint)
        self.assertNotEqual(self.labels["lem:edited"]["fingerprint"], fingerprint)
        self.assertNotEqual(self.labels["prop:twin"]["fingerprint"], fingerprint)

    def test_an_error_myst_reports_is_an_error_here(self):
        """A bodiless directive is dropped from the tree; only MyST's own output says so."""
        self.assertIn("MyST: modules/01-second.md:18 required body not provided for "
                      "directive: prf:corollary", self.text)
        self.assertNotIn("cor:bodiless", self.labels)


class FingerprintTests(unittest.TestCase):
    def test_a_reference_is_its_target_not_the_page_the_target_lives_on(self):
        reference = {"type": "crossReference", "identifier": "prop:a", "kind": "proof:lemma"}
        claim = {"type": "proof", "kind": "lemma", "children": [reference]}
        moved = {**claim, "children": [{**reference, "url": "/other", "remote": True}]}
        self.assertEqual(manuscript.fingerprint(moved), manuscript.fingerprint(claim))

    def test_a_link_to_a_heading_is_its_label_not_the_heading_text(self):
        """[](#sec:x) to a heading on another page is a link carrying the heading's text:
        renaming the heading must not change the statement. A link to a URL is kept."""
        def claim(link):
            return {"type": "proof", "kind": "lemma", "children": [
                {"type": "paragraph", "children": [{"type": "text", "value": "See "}, link]}]}
        def section(title):
            return {"type": "link", "identifier": "sec:x", "label": "sec:x", "url": "/other",
                    "children": [{"type": "text", "value": title}]}
        self.assertEqual(manuscript.fingerprint(claim(section("Old title"))),
                         manuscript.fingerprint(claim(section("New title"))))
        self.assertNotEqual(manuscript.fingerprint(claim(section("Old title"))),
                            manuscript.fingerprint(claim({**section("Old title"),
                                                          "identifier": "sec:y"})))
        def external(text):
            return {"type": "link", "url": "https://example.org",
                    "children": [{"type": "text", "value": text}]}
        self.assertNotEqual(manuscript.fingerprint(claim(external("a"))),
                            manuscript.fingerprint(claim(external("b"))))

    def test_a_displayed_status_is_not_part_of_the_statement(self):
        """scripts/status.mjs adds the status to a claim's title, or a title holding only
        the status; neither changes the fingerprint, so a status change lifts nothing."""
        text = {"type": "paragraph", "children": [{"type": "text", "value": "Let x."}]}
        status = {"type": "span", "claimStatus": True,
                  "children": [{"type": "text", "value": "Not settled here"}]}
        title = {"type": "admonitionTitle", "children": [{"type": "text", "value": "Bound"}]}
        claim = {"type": "proof", "kind": "lemma", "children": [title, text]}
        titled = {**claim, "children": [{**title, "children": [*title["children"], status]},
                                        text]}
        bare = {"type": "proof", "kind": "lemma", "children": [text]}
        created = {**bare, "children": [{"type": "admonitionTitle", "claimStatus": True,
                                         "children": [status]}, text]}
        self.assertEqual(manuscript.fingerprint(titled), manuscript.fingerprint(claim))
        self.assertEqual(manuscript.fingerprint(created), manuscript.fingerprint(bare))


class ManuscriptAbsenceTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_a_tree_without_myst_yml_has_no_manuscript_and_no_error(self):
        errors: list[str] = []
        self.assertEqual(manuscript.manuscript_labels(self.root, errors), {})
        self.assertEqual(errors, [])

    def test_a_missing_myst_is_an_error_that_says_how_to_install_it(self):
        write_myst_project(self.root)
        errors: list[str] = []
        with mock.patch.object(manuscript, "myst_command", return_value=None):
            self.assertEqual(manuscript.manuscript_labels(self.root, errors), {})
        self.assertIn("MyST is required", "\n".join(errors))
        self.assertIn("npm ci", "\n".join(errors))


if __name__ == "__main__":
    unittest.main()
