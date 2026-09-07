# Changelog

All notable changes to the conjecture-search template are recorded here. Each released section
corresponds to the Git tag with the same version.

The template is pre-stable. Until `v1.0.0`, increment the minor version for a feature or a change
that requires forks to migrate, and increment the patch version for a backward-compatible fix.
Batch related breaking changes into one minor release. Publish `v1.0.0` only when the template
contract is intended to remain stable; from that point onward, use standard semantic versioning.

## [Unreleased]

### Added

- Add a `check` workflow that validates the repository, the worked example and the checker's
  test suite on pull requests into the default branch.

### Changed

- Publish the site only on an explicit manual dispatch. The `site` workflow no longer runs on
  push or pull request, so no revision is built or deployed unless a human asks for it.

## [0.1.0] - 2026-09-04

### Added

- Require explicitly delimited metadata blocks in proof and refutation dossiers, so narrative
  comments cannot be interpreted as header fields.
- Treat numbered equations, alignments, figures, and tables nested inside claims as structural
  labels owned by those environments.

### Changed

- Replace control-plane decision records with this package-level changelog and Git tags.
- Keep the documentation link checker focused on live documentation while exempting immutable
  search checkpoints and proof reviews.
- Make capability-pack installation tests independent of which packs are installed in the host
  repository.
- Validate numerical `instance` observations at artifact write time.
- Correct live role and lens references to the current universal constraint order.

### Removed

- Remove the constraint-citation index and its `check.py constraints` command.
- Remove the `decisions/` control-plane archive and its contribution workflow.

### Fixed

- Keep installed capability-pack roles synchronized with their pack sources.
- Remove the synthesizer's stale reference to the retired decisions archive.
- Verify the byte-preserved source and checksum declared by migrated numerical artifacts.

[Unreleased]: https://github.com/numina-functional-inequalities/conjecture-search-template/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/numina-functional-inequalities/conjecture-search-template/releases/tag/v0.1.0
