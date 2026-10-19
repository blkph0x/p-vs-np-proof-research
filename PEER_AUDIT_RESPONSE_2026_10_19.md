# Response to the 19 October peer audit

The audit is correct about the project's narrow contribution and its limits.
No public repository search can establish that no one has ever assembled a
similar collection, so the landing-page language now describes the repository
as a scoped certificate ledger rather than claiming absolute novelty. The
actual rule is precise: a stored outcome is an exact certificate for the
declared model, an explicit `UNKNOWN`/`UNKNOWN_CAP` outcome with its boundary,
or it is not promoted to a result.

## What the neighboring projects provide

| Neighbor | What it contributes | Boundary relative to this repository |
| --- | --- | --- |
| [Proof Complexity Zoo](https://proofcomplexityzoo.gitlab.io/zoo/) | A map of proof systems and simulations. | It is a literature map, not the finite certificate/replay ledger here. |
| [SAT Competition](https://satcompetition.github.io/) and [DRAT-trim](https://github.com/marijnheule/drat-trim) | Industrial SAT solving and checking of individual UNSAT proof traces. | Checking one formula does not classify a relaxation or prove a complexity theorem. |
| [cake_lpr](https://github.com/marijnheule/cake_lpr) | A formally oriented checker for proof formats used by SAT solvers. | Its proof object is a formula-level certificate, not the quotient LP certificates recorded here. |
| [Sherali--Adams](https://doi.org/10.1016/0166-218X(92)00190-W) and [Schoenebeck's Lasserre lower bounds](https://schoeneb.people.si.umich.edu/papers/LasserreNew.pdf) | Strong hierarchy theorems, integrality gaps, and numerical or exact tools in their stated settings. | This repository records one small exact rational quotient and its independently rebuilt matrix; it does not replace those theorems or claim a new hierarchy lower bound. |
| Reed--Muller coding literature, including [Reed's original paper](https://doi.org/10.1109/TIT.1954.1057465) | Code parameters, distance, decoding, and local tests. | The local-marginal quotient and its finite certificates are a separate diagnostic model. |
| [Dantchev's matching-principle notes](https://www.brics.dk/DS/02/2/BRICS-DS-02-2.pdf) | The PHP width construction replayed by the proof-complexity lab. | The repository replays bounded instances and the stated uniform construction; it does not claim ownership of the theorem. |

The academic hierarchy results are stronger wherever their hypotheses apply.
The RM(2,5) calculations do not supersede Schoenebeck-style lower bounds,
LP-decoding results, or the broader sum-of-squares literature. They make one
finite case exact and auditable.

## What the repository actually adds

The value is epistemic and operational. A second program reconstructs the
finite geometry, scope orbits, quotient matrix, rational equations, and dual
reduced costs without importing the producer's model builder. The one-cut,
two-cut, three-cut, four-cut, five-cut, and now six-cut RM(2,5) records therefore expose exact objects that
another person can inspect or mutate. The new third-cut certificate adds the
valid integer polynomial `(t-6)(t-7)(t-23)(t-24)`, which the two-cut witness
evaluates at `-2400/19`, and closes the next finite relaxation at `5231/801`
with zero primal/dual gap.

Failure remains data. The bounded XOR-chain and role-search branches preserve
`UNKNOWN_CAP`; a negative pseudo-expectation is reported as a violated cut,
not as a claim that all degree-two moments are integral; a dual-distance
argument is not promoted to a general SAT lower bound. Exact arithmetic,
explicit support, mutation tests, and independent replay are acceptance
conditions, not decoration.

## What it does not establish

The repository does not present a stronger proof system than Cutting Planes,
Frege, sum-of-squares, or the systems catalogued by the Zoo. Two Python
programs can share a mistaken definition, so independent replay is a useful
check rather than a proof-assistant trust theorem. The finite PHP and
Reed--Muller records are replays of scoped results, not replacements for the
original all-size papers. A journal article would be easier to cite than a
commit history; this response and the linked reports are intended to make the
current record citable while that longer-form work is absent.

## Corrections made in this checkpoint

- Updated the site, README, report, and reproducibility date to 19 October
  2026 and corrected the audit total to 52 suites and 522 test methods.
- Added the exact three-cut producer, pure-standard-library independent
  reviewer, adversarial tests, report, CI replay step, and audit registration.
- Reworded the affine-overlap and flat-star historical reports so their
  scope-specific `UNRESOLVED` fields are not mistaken for the current status
  of the later full level-eight replay.
- Added the exact four-cut producer, independent reviewer, adversarial tests,
  report, CI replay step, and audit registration. The new integer-domain cut
  `t(31-t)(t-3)(t-4)(t+28)` closes the next finite relaxation at
  `1219047171/184149541`; this remains a scoped certificate.
- Added the exact fifth-cut producer, independent reviewer, adversarial tests,
  report, CI replay step, and audit registration. The core integer-domain cut
  `t(31-t)(t-3)(t-4)` is violated by the four-cut witness at
  `-61440933600/184149541` and closes the next finite relaxation at
  `324713143/48731153`; this remains a scoped certificate.
- Added the exact sixth-cut producer, independent reviewer, adversarial tests,
  report, CI replay step, and audit registration. The valid product
  `(t-6)(t-7)(31-t)(t+32)^2` is violated by the fifth-cut witness at
  `-6759234824400/48731153` and closes the next finite relaxation at
  `22465669893401/3255387995415`; this remains a scoped certificate.
- Added the three-cut result to the local lab documentation and public method
  narrative. `P versus NP remains unresolved`.

The project's source policy remains in [`CITATIONS.md`](CITATIONS.md), and the
generated URL index is [`PUBLIC_SOURCES.md`](PUBLIC_SOURCES.md). The exact
certificate files and replay commands are linked from the
[`six-cut report`](local_marginal_code_lab/REED_MULLER_SOS_SIX_CUT_REPORT.md),
which follows the five-cut, four-cut, and three-cut reports.
