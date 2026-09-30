// A MyST plugin: every labelled statement shows its status, read from the ledger at build
// time. A statement's status is therefore never written by hand, and never stale.
//
//   Not settled here   the ledger says open: not established in this project, which
//                      says nothing of the literature
//   Proved             links to the first dossier a proof record names (none: a literature proof)
//   Refuted            links to the first refuter in refuted_by
//
// A definition shows no status: its kind says enough. After the status comes the
// statement's label, which a reader quotes to name it, and — when `project.github` in
// myst.yml names the repository — links that open an issue form with the label filled
// in: "Idea" and "Counterexample" on an open statement, "Correction" on any other. Every
// node this plugin adds carries `claimStatus: true`, and the checker's statement
// fingerprint ignores it, so neither a status change nor a new repository lifts a
// certification. The ledger and myst.yml are read relative to the directory MyST runs
// in, the project root; without a ledger the plugin does nothing.
import fs from 'node:fs';
import path from 'node:path';
import { load } from 'js-yaml';

const LEDGER = 'research/program/ledger.yaml';
const CONFIG = 'myst.yml';

function readYaml(file) {
  try {
    return load(fs.readFileSync(file, 'utf8')) ?? {};
  } catch {
    return null;
  }
}

function readLedger() {
  const nodes = readYaml(LEDGER)?.nodes ?? [];
  return new Map(nodes.filter((node) => node?.id).map((node) => [node.id, node]));
}

// The repository URL, or null while myst.yml names none (or keeps a placeholder).
function readRepository() {
  const url = readYaml(CONFIG)?.project?.github;
  return typeof url === 'string' && /^https:\/\/github\.com\/[^<>\s]+$/.test(url)
    ? url.replace(/\/+$/, '')
    : null;
}

const text = (value) => ({ type: 'text', value });

function status(node, file) {
  if (node.status === 'open') return [text('Not settled here')];
  if (node.status === 'proved') {
    const artifact = (node.proofs ?? []).find((record) => record?.artifact)?.artifact;
    if (!artifact) return [text('Proved')];
    const url = path.relative(path.dirname(file), path.resolve(artifact));
    return [{ type: 'link', url, children: [text('Proved')] }];
  }
  if (node.status === 'refuted') {
    const refuter = (node.refuted_by ?? [])[0];
    if (!refuter) return [text('Refuted')];
    return [text('Refuted by '), { type: 'crossReference', identifier: refuter, label: refuter }];
  }
  return [];
}

// The issue forms of .github/ISSUE_TEMPLATE, each with a `statement` field.
function forms(node, repository) {
  if (!repository) return [];
  const chosen = node.status === 'open'
    ? [['Idea', 'open-problem-idea.yml'], ['Counterexample', 'counterexample.yml']]
    : [['Correction', 'correction.yml']];
  const statement = encodeURIComponent(node.id);
  return chosen.map(([name, form]) => ({
    type: 'link',
    url: `${repository}/issues/new?template=${form}&statement=${statement}`,
    children: [text(name)],
  }));
}

function* statements(tree) {
  if (tree?.type === 'proof' && tree.label && tree.kind !== 'proof') yield tree;
  for (const child of tree?.children ?? []) yield* statements(child);
}

const statusTransform = {
  name: 'claim-status',
  stage: 'document',
  plugin: () => (tree, file) => {
    const ledger = readLedger();
    if (!ledger.size) return;
    const repository = readRepository();
    for (const statement of statements(tree)) {
      const node = ledger.get(statement.label);
      if (!node) continue;
      const parts = [
        status(node, file.path ?? '.'),
        [{ type: 'inlineCode', value: node.id }],
        ...forms(node, repository).map((link) => [link]),
      ].filter((part) => part.length);
      const children = parts.flatMap((part, i) => (i ? [text(' · '), ...part] : part));
      let title = statement.children?.find((child) => child.type === 'admonitionTitle');
      const span = { type: 'span', class: 'claim-status', claimStatus: true, children };
      if (title) {
        span.children = [text(' — '), ...children];
        title.children = [...(title.children ?? []), span];
      } else {
        title = { type: 'admonitionTitle', claimStatus: true, children: [span] };
        statement.children = [title, ...(statement.children ?? [])];
      }
    }
  },
};

export default { name: 'Statement status', transforms: [statusTransform] };
