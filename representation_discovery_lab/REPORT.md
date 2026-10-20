# Hidden-affine representation discovery experiment

The repaired structural baseline returns an exact projected equation only when
it has accounted for the complete original CNF. It recognizes complete even-XOR
triples plus one distinct unit, and proves every helper expression by acyclic
substitution. Unsupported structure returns `UNKNOWN`, with no equation claim.
This is a bounded representation experiment, not a SAT or P-versus-NP result.

The original family is one even-parity equation on `m` shared variables encoded
by a chain of 3-CNF XOR gadgets and `m-1` existential helpers. It has a short
one-equation projection. The saved instances have `m=3..7`, with identity and
reversed input orders. All saved original clauses, ordered shared/local IDs and
projected truth values are included in `RESULTS.json`.

## Correctness repair

The previous baseline silently skipped unrecognized clauses. For example, adding
`(x0 OR x1)` to the three-variable chain removes the all-zero projected solution,
but the old baseline still returned its original even-parity equation. The
repair requires every nontrivial clause to be a unit or part of a fully checked
four-clause XOR group. An empty clause, binary clause, incomplete/changed gadget,
or unresolved equation causes `UNKNOWN`. The recognizer deliberately remains
incomplete: `UNKNOWN` does not mean non-affine, unsatisfiable or hard.

The positive-unit index was also incorrect: it used `-literal-1` rather than
`abs(literal)-1`. Positive units now recover odd parity correctly. Shared IDs
must be distinct nonnegative exact integers, and literals must be nonzero exact
integers; booleans, floats, strings and malformed clause containers raise
`ValueError`. Equation support indexes the supplied shared order, rather than
raw variable IDs. Shared variables absent from the CNF remain free.

Repeated literals, duplicate clauses and repeated copies of the same unit are
normalized safely. Tautologies are checked and discarded as true clauses; they
cannot conceal another uncovered clause. All remaining units must be the same
unit. Empty formulas, contradictory units and other unsupported structures
return `UNKNOWN` rather than inventing a single equation.

The exhaustive `project` API also validates literal coverage and requires the
shared/local ID lists to be unique and disjoint, preventing local assignments
from overwriting a shared coordinate. Constructor permutations and renamings
no longer silently coerce noninteger IDs.

Why an exact structural answer is sound: initialize the ordered shared bits as
independent affine expressions. Every eliminated gadget defines exactly one
fresh helper from two already known expressions. Thus every shared assignment
extends uniquely to all variables of every recognized gadget, with no hidden
additional equation. Complete clause coverage and no remaining gadgets leave
only the checked unit constraint. Substituting its target expression gives the
returned equation. If any step cannot establish this argument, the baseline
returns `UNKNOWN`.

The legacy status name `EXACT_AFFINE` means an exact XOR equation, and does
not assert a nonempty affine coset. The XOR of an empty support is zero:
empty support with `rhs=0` describes every shared assignment, while empty
support with `rhs=1` describes no assignments. A regression constructs
`h=x0 XOR x1`, `g=x0 XOR h`, `t=x1 XOR g=0` and checks both unit polarities
against the complete original projection. This is distinct from recognition
APIs elsewhere that reserve affine-coset output for nonempty relations.

## Two different cost proxies

`enumeration_discovery_work` and `exhaustive_replay_work` are symbolic charges
for a declared fully exhaustive, non-short-circuit schedule. They are not
instrumentation counts of the Python implementation. Actual projection uses
short-circuit satisfaction and existential search; `discover` checks that its
projection equals the family's expected parity. It calculates the complete
candidate-vocabulary schedule algebraically; it does not execute that candidate
search or discover an arbitrary unknown representation.

| shared variables | helpers | clauses | encoded bits | symbolic discovery schedule | symbolic replay schedule |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 3 | 2 | 9 | 15 | 408 | 288 |
| 4 | 3 | 13 | 17 | 2,160 | 1,664 |
| 5 | 4 | 17 | 24 | 10,720 | 8,704 |
| 6 | 5 | 21 | 27 | 51,136 | 43,008 |
| 7 | 6 | 25 | 30 | 237,440 | 204,800 |

For this declared schedule:

```text
local variables            = m - 1
CNF clauses                = 4m - 3
encoded bits               = 9 + m ceil(log2 m)
full replay charge         = (4m - 3) 2^(2m - 1)
candidate-vocabulary charge = (2^(m + 1) - 1) 2^m
full discovery charge      = full replay charge + candidate-vocabulary charge
```

The representation bit count is this repository's support-label encoding,
not a proof of minimum encoding length. The symbolic schedule has
Theta(m 4^m) charged units while that particular encoding has Theta(m log m)
bits; neither statement lower-bounds a different discovery algorithm.

The baseline `work` counter now includes all of these loop visits:

- one per shared ID during validation;
- one per raw clause, raw literal and distinct-literal tautology check;
- one per normalized clause and each of its literals during classification;
- one per candidate triple group;
- for a four-clause group, all eight truth assignments, three assignment stores,
  four clause visits and twelve literal visits per assignment (160 units);
- expression initialization, every substitution pass, every pending equation
  and each of its three variable visits, including failed scans;
- one per successful substitution and each final shared-position output scan.

Sorting, hashing, allocation, interpreter overhead and arbitrary-length integer
operations are not fully charged. This is an auditable logical-operation proxy,
not CPU time, memory use or a universal complexity measure. The independent
review recomputes it, including failed scans. Its units differ from the symbolic
enumeration schedule; comparing their numeric values is not a speed claim.
Each successful pass removes a gadget, so the number of substitution scans is
polynomial, even when input renaming forces repeated passes. The structural
baseline is consequently a polynomial control for the supported family.

## Saved controls and independent verification

Seven original-input controls cover reversed gadget blocks, a duplicated gadget,
bijective renaming, a positive unit, an added restricting binary clause, an
added empty clause, and a duplicated unit plus tautology. The two added-clause
controls must return `UNKNOWN`; the others produce independently checked exact
projections. The nonlinear CNF `(x0 OR x1) AND (x0 OR x2)` is evaluated from its
actual clauses; translated support closure proves its projection non-affine,
and the structural baseline returns `UNKNOWN`.

`independent_review.py` imports no producer module. It constructs XOR clauses
by excluding odd assignments, reconstructs every saved original/control, and
enumerates complete original assignments before comparing any exact equation.
It independently checks the nonlinear projection/closure and computes gadget
validity from forbidden assignment masks. It separately reconstructs the
published baseline scan schedule. Malformed or changed originals, claimed
relations, coverage, metadata and charges are tested by saved-payload mutations.

The regression suite also checks all 512 subsets of the eight three-variable
clauses with both target units, plus 180 seeded small acyclic originals with
variable renaming and restricting-clause controls. Every exact answer is compared
with an independent full-assignment projection oracle. These finite checks
support the coverage/substitution argument; they do not make this recognizer
complete for general affine projections.

Reproduce with `python run_experiment.py`, `python -m unittest discover -v`, and
`python independent_review.py` in this directory. The saved source map binds all
implementation, test, review and report files and confirms source stability.
No archive manifest, old lab, commit or remote is changed by these commands.

Source hashing uses the explicit scheme `sha256-utf8-lf-v1`: decode strict
UTF-8, replace CRLF and lone CR line endings with LF, re-encode UTF-8, then
hash with SHA-256. No trimming, Unicode normalization or BOM removal occurs;
all other content changes alter the hash. This makes evidence portable across
Git's text line-ending conversion. `source_unchanged_during_run` means equality
of this normalized text, rather than byte-for-byte equality of newline styles.
Producer and independent replay implement the same documented scheme separately.
Regression tests replay complete LF and CRLF source snapshots against the saved
hashes and reject an actual source edit; they also check significant whitespace,
BOM and UTF-8 validation behavior.
