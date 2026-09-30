// A MyST plugin: every labelled statement shows its status, read from the ledger at build
// time. A statement's status is therefore never written by hand, and never stale.
//
//   Not settled here   the ledger says open: not established in this project, which
//                      says nothing of the literature
//   Proved             links to the first dossier a proof record names (none: a literature proof)
//   Refuted            links to the first refuter in refuted_by
//
// A definition shows nothing: its kind says enough. Every node this plugin adds carries
// `claimStatus: true`, and the checker's statement fingerprint ignores it, so a status
// change never lifts a certification. The ledger is read relative to the directory MyST
// runs in, the project root; without one the plugin does nothing.
import fs from 'node:fs';
import path from 'node:path';
import { load } from 'js-yaml';

const LEDGER = 'research/program/ledger.yaml';

function readLedger() {
  let text;
  try {
    text = fs.readFileSync(LEDGER, 'utf8');
  } catch {
    return new Map();
  }
  const nodes = (load(text) ?? {}).nodes ?? [];
  return new Map(nodes.filter((node) => node?.id).map((node) => [node.id, node]));
}

function badge(node, file) {
  const text = (value) => ({ type: 'text', value });
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
  return null;
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
    for (const statement of statements(tree)) {
      const node = ledger.get(statement.label);
      const children = node && badge(node, file.path ?? '.');
      if (!children) continue;
      let title = statement.children?.find((child) => child.type === 'admonitionTitle');
      const status = { type: 'span', class: 'claim-status', claimStatus: true, children };
      if (title) {
        status.children = [{ type: 'text', value: ' — ' }, ...children];
        title.children = [...(title.children ?? []), status];
      } else {
        title = { type: 'admonitionTitle', claimStatus: true, children: [status] };
        statement.children = [title, ...(statement.children ?? [])];
      }
    }
  },
};

export default { name: 'Statement status', transforms: [statusTransform] };
