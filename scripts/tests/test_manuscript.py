"""The manuscript lane's reader: MyST's tree turned into anchors, and what it refuses.

One real MyST project is built once for the whole class, holding every case at the same
time — a MyST build is the slow part, and these assertions only read its result. The lane
rules that consume the anchors are tested in ``test_core.py`` without a build.
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
        self.assertEqual(self.labels["lem:anchored"],
                         {"kind": "lemma", "file": "modules/00-first.md"})
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

    def test_labels_whose_html_anchors_collide_are_an_error(self):
        self.assertIn("label 'a-b:c' and label 'a:b-c' share the HTML anchor '#a-b-c'",
                      self.text)

    def test_an_error_myst_reports_is_an_error_here(self):
        """A bodiless directive is dropped from the tree; only MyST's own output says so."""
        self.assertIn("MyST: modules/01-second.md:18 required body not provided for "
                      "directive: prf:corollary", self.text)
        self.assertNotIn("cor:bodiless", self.labels)

    def test_the_html_anchor_mirrors_myst(self):
        self.assertEqual(manuscript.html_id("conj:example"), "conj-example")
        self.assertEqual(manuscript.html_id("Thm:A__b"), "thm-a-b")
        self.assertEqual(manuscript.html_id("1:x"), "id-1-x")


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
