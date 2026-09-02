---
type: audit
date: "2026-09-02"
---

# Mathematical research modes and harness coverage

## Scope

This is a read-only design audit of the template as a general harness for mathematical research.
It records observations only: it certifies no proof and adopts no harness change. The repository
was inspected through its root contract, ledger schema, role contracts, proof and review planes,
exploration log, and numerical artifact contract. External references were consulted to compare
the template with established modes of mathematical practice.

## Overall assessment

The template is a strong harness for a theorem-centred research program in which agents attack
precise claims, record failed attempts, produce natural-language proof dossiers, and submit those
proofs to independent review. It is not yet neutral across all forms of mathematical research.

This distinction is substantive. Gowers distinguishes problem-solving from theory-building
cultures, while emphasizing that both occur in mathematics. Thurston argues that mathematical
progress also includes forms of understanding not captured by formal proofs of theorems. The
template's universal workflow, by contrast, begins from sharpening or confirming a target or
supplying a proof dossier, and therefore privileges problem-centred research.

## Research modes and present coverage

| research mode | typical durable output | appropriate validation | present fit |
|---|---|---|---|
| direct problem solving | lemmas, reductions, theorem, proof | independent proof review | strong |
| proofs and refutations | counterexamples, corrected conjectures, new hypotheses | exact witness plus checked proof | strong |
| quantitative refinement | better constants, rates, ranges, extremizers, stability results | proof or rigorous computation | partial |
| theory-building | definitions, constructions, equivalences, organizing principles | coherence, examples, consequences, later theorems | weak to partial |
| experimental mathematics | tables, plots, symbolic searches, conjectures | reproducibility first; proof later | strong |
| computer-assisted proof | reduction, exact or interval computation, certificate and checker | replayed certificate or verified implementation | poor |
| formalized mathematics | formal definitions and kernel-checked proofs | reproducible proof-assistant build | nominal support only |
| classification and enumeration | object catalogue, completeness theorem, generated dataset | generator and checker plus completeness proof | weak |
| algorithmic mathematics | algorithm, construction, correctness and complexity theorem | proof, executable tests, benchmarks | weak |
| literature synthesis | imports, normalization maps, precise remaining gaps | source-level verification | strong |
| exposition and conceptual understanding | alternative proof, survey, conceptual compression | expert review and mathematical usefulness | weak |
| applied mathematical modeling | model, calibration, prediction, sensitivity and uncertainty | data validation and uncertainty analysis | outside the present epistemology |
| foundations and independence | relative consistency, equivalence, independence from axioms | metamathematical proof | awkward under current conditional semantics |

## Strengths worth preserving

- Accepted mathematical prose, logical state, proof artifacts, numerical diagnostics, and history
  have distinct sources of truth.
- Failed approaches are durable research knowledge rather than discarded conversation.
- Structural validation is explicitly separated from mathematical correctness.
- Proof authorship and certification are separated.
- Numerical evidence carries provenance and cannot silently become a theorem.
- Shared write points and convergence are controlled explicitly.
- A counterexample candidate has a disciplined route to a certified refutation.
- Literature work distinguishes source class, normalization, and the remaining gap.

## Principal design findings

### 1. Conditional truth and current applicability are conflated

The contract requires a proved implication $H\Rightarrow C$ to remain `conditional` until $H$ is
discharged. Mathematically, however, the implication may be an unconditional theorem even while
$H$ is open. The harness should distinguish whether the implication is proved from whether it is
currently applicable. The issue also affects relative results, axiomatic mathematics, reductions
between open conjectures, and independence arguments.

### 2. Exploratory numerics and certifying computation need different channels

The current numerical boundary is correct for sampling, plots, floating-point diagnostics, MCMC,
finite testing, and conjecture generation. It is too broad for exhaustive enumeration, interval
arithmetic, SAT or SMT certificates, Gröbner-basis certificates, and other computations whose
outputs can be checked as proof objects. The non-certifying numerical harness should remain, but a
separate proof-producing computation channel is needed.

### 3. Lean certification is structural rather than executable

The ledger requires an adjacent `.lean` file for `checked_by: lean`, but the global check lane does
not compile Lean. Genuine formal certification requires a pinned toolchain and library revision, a
declared theorem, and a reproducible build in continuous integration. Formalization should also be
allowed to feed corrections back into the natural-language blueprint.

### 4. The ledger mixes orthogonal concepts

`proved`, `open`, and `refuted` describe logical standing; `imported` describes provenance;
`defined` describes the nature of an object; and `conditional` combines logical standing with
dependency readiness. A general harness should distinguish artifact kind, mathematical standing,
provenance, validation method, and applicability.

### 5. Theory-building lacks a suitable incubation form

Definitions, equivalent formulations, canonical examples and nonexamples, constructions,
analogies, desiderata, and universal properties may be valuable before any later claim depends on
them. A candidate consisting only of an id and a statement cannot carry all of this. Dependency is
also not by itself the right promotion criterion; stability, importance, and program commitment
matter.

### 6. Alternative proofs and proof improvement are not first-class

One theorem may have several valuable active proofs: conceptual, elementary, constructive,
effective, quantitative, independent, or formally verified. A single active `solution` pointer
does not naturally record these proof-level contributions or their different reviews.

### 7. Some mathematical outputs are artifacts rather than statements

Generated classifications, mathematical databases, algorithms, reference implementations,
formal libraries, machine-readable examples, and proof certificates need stable identities,
provenance, and validation without being forced to masquerade as theorem statements. A broad
harness needs an artifact graph as well as a claim graph.

### 8. Applied modeling has a different epistemology

A model can be mathematically correct yet empirically inadequate. Applied work needs data
provenance, calibration, model discrepancy, sensitivity, uncertainty, prediction scope, and
empirical validation. These do not fit honestly into a `proved`/`open`/`refuted` claim status.

## Design direction suggested by the audit

Do not encode every research mode as another agent role. Roles describe who performs work; they
should not define what mathematical knowledge is. Preserve the theorem-oriented core and describe
research through orthogonal dimensions:

- intent: solve, build theory, classify, compute, formalize, model, explain;
- output: claim, definition, proof, example, construction, algorithm, model, dataset, certificate;
- maturity: lead, candidate, precise, active, superseded;
- logical standing: open, established, refuted, independent;
- validation: human review, agent review, formal kernel, certificate checker, reproducible
  experiment, empirical validation;
- relations: proves, uses, implies, refines, generalizes, specializes, contradicts, tests,
  generates.

For a program in functional inequalities, the likely useful scope is a theorem-centred core with
optional support for experimental mathematics, rigorous computer-assisted proof, and
formalization. Applied modeling and mathematical databases can share provenance and append-only
history principles without necessarily sharing the same epistemic schema.

## References consulted

- William P. Thurston, [*On proof and progress in mathematics*](https://arxiv.org/abs/math/9404236).
- W. T. Gowers, [*The Two Cultures of Mathematics*](https://www.maths.tcd.ie/~bnick/Gowers.pdf).
- John Worrall, [overview of Lakatos's *Proofs and Refutations*](https://www.rep.routledge.com/articles/biographical/lakatos-imre-1922-74/v-1/sections/proofs-and-refutations-contributions-to-philosophy-of-mathematics).
- David H. Bailey and Jonathan M. Borwein, [*Experimental Mathematics: Examples, Methods and Implications*](https://escholarship.org/uc/item/6b6986dn).
- Thomas Hales et al., [*A formal proof of the Kepler conjecture*](https://arxiv.org/abs/1501.02155).
- [General Polymath rules](https://polymathprojects.org/general-polymath-rules/).
- [LMFDB development guidelines](https://github.com/LMFDB/lmfdb).
- E. Bruce Pitman, [*Model Uncertainty: Mathematical and Statistical*](https://www.siam.org/publications/siam-news/articles/model-uncertainty-mathematical-and-statistical/).

## Outcome

This audit recommends no immediate file or schema change. The intended scope of the template
should be fixed before implementation work begins.
