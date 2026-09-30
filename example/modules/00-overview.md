% The worked example's manuscript, in four modules. Every labelled claim directive is a
% node in example/research/program/ledger.yaml with the same id, and its content is fixed;
% the prose around it is the writer's. Heading labels are structural. The statuses shown
% next to each statement come from the ledger (scripts/status.mjs): prose never states one.
%
% Between them the modules hold one instance of each case the harness knows: a proved
% statement with a dossier, a proved fence (prop:upper-constant, bounding conj:example),
% an open conjecture under an open fence (conj:weighted-example under
% conj:weighted-upper), and a conjecture refuted by a proved refuter.

(sec:overview)=
# How much does centring cost?

+++ {"part": "abstract"}

Subtracting the mean from a list of real numbers lowers its sum of squares by an exact
amount. We ask whether a fixed fraction of the sum always survives, and find that none
does: constant vectors lose everything. A worked example, deliberately elementary, so that
the shape of the document is what you look at.

+++

## The question

Centring a list of numbers — subtracting its mean — is the first step of almost every
statistical computation. Throughout, $a_1,\dots,a_n$ are real numbers, $n \ge 1$, and
$\bar a = \frac1n\sum_{i=1}^n a_i$ is their mean. Centring changes the sum of squares, and
it is natural to ask by how much. Can it destroy most of a vector's energy, or does a
fixed fraction always survive? The conjecture examined here proposed the fraction one
half: [](#conj:example).

Take $a = (1, 2, 3)$. The mean is $\bar a = 2$, the centred vector is $(-1, 0, 1)$, and

$$
\sum_i (a_i - \bar a)^2 = 2, \qquad \sum_i a_i^2 = 14 .
$$

Only $2/14 = 1/7$ of the sum of squares survives, already less than one half. The loss is
$12 = 3 \cdot 2^2 = n \bar a^2$, and that is no accident.

## The answer, in short

The loss is always exactly $n\bar a^2$ ([](#prop:example)), so centring never increases
the sum of squares ([](#prop:upper-constant)). It is largest, relative to
$\sum_i a_i^2$, for a constant vector $a = (t, \dots, t)$: the centred vector is zero and
everything is lost. No positive fraction survives ([](#prop:example-refuter)).
[](#sec:centring) proves the identity and the bound, [](#sec:refutation) builds the
counterexample, and [](#sec:open) states a question this document leaves unsettled — a
classical one, kept as an example of the form.

## How to read the statements

Each statement shows its status next to its title — not settled here, proved or refuted —
and a proved statement links to its complete written proof. *Not settled here* means that
this document neither proves nor refutes the statement; it says nothing of the literature.
Which statements are genuine research problems, the prose says. A proof counts only once a reviewer other
than its author has checked it against the statement, and the check is recorded. If a
statement is edited afterwards, its proof counts as unchecked until it is reviewed again.
Computations can suggest where to look, but they never count as proof; where the text
reports one, it says so.

Contributions — a proof, a counterexample, a reference we missed, a correction — are
welcome by e-mail at `contact@example.org` or as an issue on the project repository. Name
a statement by its label, for instance `conj:weighted-example`.
