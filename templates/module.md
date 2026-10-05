% Copy to modules/<NN-slug>.md. Every labelled claim directive here is exactly one ledger
% node with the same id; a heading, equation or prf:remark label is structural. See
% SPECIFICATION.md, Formats → Ledger and Manuscript.
%
% The content of a labelled directive, its title included, is the statement: only the
% orchestrator writes it. Everything else — headings, prose, examples, remarks, the order
% of sections — is the writer's, for a mathematician who has never seen this repository.
% The displayed status comes from the ledger. Prose may describe it when consistent and
% linked to the claim ([](#conj:main)); open here need not mean open in the literature.
% Notes for agents go in % comments.

(sec:slug)=
# Title

Why the question matters, and an example worked by hand before the general statement. A
fixed normalization is not prose: state it in a `prf:definition` under its own `:label:`,
whose node has `status: defined`.

:::{prf:conjecture}
:label: conj:main
The precise quantified statement. This text is canonical.
:::

What the statement says in words, and where it comes from.

% The bold paragraphs below are optional: keep those the statement calls for, in any order.
% After a proved statement: its idea of proof, then what is sharp or fails to extend.
% After a statement the project has not settled: why it matters, the evidence, where to
% start. Say before the statement whether it is a research problem or only not done here.

**Idea of the proof.** The mechanism in a few lines, for a reader who will not open the
full proof: the one estimate or construction that carries it. The full proof is linked
from the statement's status.

**Limits.** Where the statement is sharp, and what fails beyond it: the example that
shows a hypothesis cannot be dropped, or the constant cannot be improved.

**Why it matters.** What the answer would change, and what it would follow from or imply.

**Evidence.** What is known for small or special cases. A computation is evidence, and
says so.

**Where to start.** The approach that looks most promising, and what has already failed.

**What remains.** The question this section leaves, and where the document takes it up.
