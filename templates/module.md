% Copy to modules/<NN-slug>.md. Every labelled claim directive here is exactly one ledger
% node with the same id; a heading, equation or prf:remark label is
% structural. See SPECIFICATION.md, Formats → Ledger.

(sec:slug)=
# Title

Orientation prose. A fixed normalization is not prose: state it in a `prf:definition` under
its own `:label:`, whose node has `status: defined`.

:::{prf:conjecture}
:label: conj:main
The precise quantified statement. This text is canonical.
:::
