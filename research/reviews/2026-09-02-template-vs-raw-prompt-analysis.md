---
type: audit
date: "2026-09-02"
---

# Template versus a conjecture-specific raw prompt

## Scope

This is a design analysis of the repository template as a harness for mathematical research,
compared with the conjecture-specific multi-agent prompt in
[`prompt_openai.md`](../../prompt_openai.md). It is not an assessment of whether the claim made in
that prompt is historically accurate, and it certifies no proof or mathematical statement.

## Overall assessment

The template adds substantial value for sustained, multi-agent mathematical research. Its main
contribution is not additional mathematical creativity; it is reliable research memory,
provenance, coordination, and epistemic discipline.

It should not replace a strong problem-specific prompt such as `prompt_openai.md`. The best design
is a precise, conjecture-specific research brief operating inside this repository template. The
two artifacts solve different problems.

| dimension | `prompt_openai.md` | repository template |
|---|---|---|
| exact target and edge cases | excellent | empty until instantiated |
| problem-specific attack strategy | excellent | mostly generic roles |
| approach diversity | explicitly required | possible, but not systematically tracked |
| persistent memory | none outside the conversation | strong append-only attempt history |
| claim and dependency tracking | informal | strong claim graph |
| proof provenance | transient adversarial audit | persisted dossier and independent review |
| numerical reproducibility | warns against finite verification | provenance-stamped harness |
| epistemic honesty | problematic termination rules | strong separation of open, proved, and refuted |
| one-shot search | efficient | potentially cumbersome |
| long-running program | fragile | much stronger |

## What the raw prompt does particularly well

The comparison prompt is not truly raw. It is a sophisticated, highly tailored search
specification.

- It gives precise definitions and quantifiers, including parallel edges, disconnected graphs,
  and exactly-two multiplicity.
- It lists insufficient outcomes explicitly, preventing special cases and reductions to equally
  hard conjectures from being presented as complete solutions.
- It prescribes genuine portfolio management: independent routes, an approach-family registry,
  reopening conditions, and protection against premature convergence.
- It supplies a problem-specific audit checklist. For the stated graph problem, checks involving
  exact-two multiplicity, repeated trails, parallel-edge cycles, cutvertices, and circularity are
  much more valuable than a generic instruction to be rigorous.

The template does not generate these problem-specific insights automatically. Its generic
`prover`, `proof-checker`, and `refutation-seeker` roles need a brief of this quality.

## Genuine value added by the template

### Persistent research memory

The validated, append-only exploration log preserves dead ends, candidates, engaged nodes, and
run artifacts across conversations. This matters in conjecture research: without durable memory,
a large parallel search can produce many variations of the same failed reduction and lose the
precise obstruction shortly afterward.

### Protection against category errors

The ledger distinguishes proof dependencies, antecedents of conditional implications,
conclusions, proved obstructions, heuristic barriers, and certified refuters. In particular, the
separation of truth from applicability allows a reduction $A\Rightarrow B$ to remain a proved
implication while $A$ remains open, without pretending that $B$ has been established.

This is safer than keeping the frontier only in an orchestrator's conversational summary.

### Proofs as durable artifacts

An internally proved claim must point to a standalone dossier and an explicit certification
record. Authorship and review are separated, with the reviewer preferably reconstructing the
proof from repository artifacts without the prover's conversation history.

This does not guarantee correctness, but it makes casual proof inflation harder: a conversational
claim that an argument seems correct cannot silently become an established result.

### Responsible computation

The numerical harness records configuration, seeds, versions, evidence classes, outcomes, and
immutable artifacts while forbidding finite agreement from becoming proof. The raw prompt also
recognizes that finite verification is insufficient, but the template additionally makes the
computation reusable and reproducible.

### Multi-agent write coordination

The single-writer ledger, concurrency keys, exclusive dossier ownership, and
orchestrator-applied deltas address a practical failure mode absent from the raw prompt: agents
concurrently producing inconsistent versions of the research state.

### An explicit boundary for automated checks

The repository correctly states that a green structural check does not establish semantic
agreement or mathematical correctness. Those remain obligations of independent review.

At the time of this audit, the read-only ledger and agent-definition validators both returned
zero errors: the worked example contained three ledger nodes and the roster contained ten roles.
The full build lane was not run because it creates build artifacts.

## Weaknesses of the raw prompt

The raw prompt has serious epistemic risks when used for real research rather than benchmark
isolation.

### It assumes the desired answer

The instruction to assume that a complete affirmative proof exists removes refutation and honest
uncertainty from the search space. It can suppress a correct diagnosis and incentivize hiding a
gap.

### Its termination rules discourage honest output

The prompt forbids returning failure or partial progress and asks for at least eight hours of
search. For a difficult conjecture, this encourages either nontermination or an overstated proof.
There is also a tension between the instruction to report the strongest rigorous derivation and
exact remaining gap if no proof survives, and the later prohibition on returning any partial
result.

Elapsed time is a weak proxy for search quality. It does not measure approach exhaustion,
duplicated work, mathematical novelty, or the value of certified intermediate results.

### Benchmark isolation is not a good research norm

Restricting literature search and forbidding agents to check whether the target remains open may
be appropriate for a controlled benchmark. In real mathematical research it encourages
rediscovery, makes source verification harder, and prevents the program from locating its actual
frontier.

## Weaknesses of the template

### Administrative overhead

The template carries thousands of lines of contracts, roles, validators, and tests. This is
excessive for a single afternoon or an elementary lemma. It becomes worthwhile when work spans
multiple agents or sessions, uses numerical runs or literature imports, or has a nontrivial
dependency graph.

The candidate mechanism usefully delays full ledger and manuscript overhead until a statement is
stable enough to deserve it, but every nontrivial attempt still acquires a durable record.

### It records attempts better than it manages a search portfolio

The raw prompt explicitly requests an approach-family registry, saturation detection, and
reopening conditions. Exploration metadata in the template records nodes, outcomes, candidates,
and artifacts, but it does not structurally record:

- the approach family or mechanism attempted;
- the precise blocking lemma;
- the condition under which the route should be reopened;
- parent and sibling approaches; or
- duplication or conceptual overlap with another attempt.

The synthesizer must therefore recover much of the search topology from prose. For a large
parallel conjecture search, this is the most important missing coordination feature.

### Process independence is not epistemic independence

Distinct author and reviewer identities and cold review contexts reduce self-review and anchoring,
but two instances of the same model may share the same blind spots. A major result still warrants
human review or genuine formal certification.

Lean support is currently structural: the ledger checks for an adjacent `.lean` file, but the
global verification lane does not compile it against a pinned toolchain and library revision.

### The template remains theorem-centred

The harness strongly supports direct proof, refutation, experimental diagnostics, and literature
synthesis. It is weaker for theory-building, classifications, algorithms, conceptual exposition,
and rigorous computer-assisted proofs whose certificates should themselves be first-class
artifacts.

This bias is largely appropriate for a program explicitly organized around proving or refuting a
conjecture, but it limits the template's claim to general mathematical research.

### Append-only memory still requires curation

Append-only records preserve provenance, but old audits and unsuccessful routes can become noisy
or misleading unless later records clearly state what they supersede. Durable memory does not
remove the need for active synthesis and candidate pruning.

## Recommended combination

Keep the template, but instantiate it with a program-specific research brief modeled on the
strongest parts of `prompt_openai.md`. That brief should contain:

1. The exact conjecture and its logical negation.
2. What counts as a complete proof and a complete refutation.
3. Problem-specific edge cases and audit tests.
4. Known equivalent-strength traps and prohibited circular reductions.
5. Initial approach families.
6. Criteria for classifying an approach as blocked and for reopening it.
7. A finite budget policy that permits the honest outcome: unresolved, with certified advances
   and exact remaining gaps.

The problem-specific brief should drive mathematical search. The repository should remember,
validate, and certify what the search produces.

## Conclusion

For a one-shot benchmark, the raw prompt may produce more mathematical pressure per token. For a
serious multi-session research program, the template is clearly more valuable, provided it is
instantiated with an equally strong problem-specific brief.

The template's value proposition is therefore not that it makes an agent more mathematically
creative. It turns a sequence of searches into an auditable research program whose claims,
failures, evidence, and certifications survive the individual conversations that produced them.
