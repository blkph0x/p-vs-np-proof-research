# Macro-assisted repeated proof-DAG scan

**Status:** completed bounded integration. No proof of P=NP or P!=NP.

The generic label-free scan of the 4,097-node width-eight proof marks 256
one-variable unit fragments `UNKNOWN` under the six-local-variable cap and two
final suffix nodes `UNKNOWN` because their leaf sub-DAGs exceed the 32-node
ancestry cap. The integration sends the first class to the certified
Hall-plus-implication unit rule and the second class to the independently
checked fused-negative-suffix rule. Every recovered relation carries its own
structural certificate; all generic records retain their original evidence.

The integrated result has 256 ordinary PB discoveries, 256 symbolic unit
discoveries, 2 symbolic suffix discoveries, and 1,792 table-only relations.
There are no remaining UNKNOWN records in this scoped 2,306-node scan. The two
suffix certificates recover a PB relation on the final two representatives and
a negative unit on the final representative. The symbolic groups receive no
reuse credit: their linear structural work is charged for every occurrence.

The independent checker replays the full 4,097-node proof, every generic
record, all 256 unit certificates, both suffix certificates, template
accounting, and forged-certificate controls. It confirms the source scan still
had 256 projection-cap and 2 sub-DAG-cap UNKNOWN cases before the structural
rules were applied. The macro changes the classification through explicit
proof-pattern checks, not by changing the generic caps or filling missing
truth-table rows.

This is a real pipeline improvement for two repeated structural families. It
does not make arbitrary residual projection polynomial, and the coNP-hard
semantic-equivalence barrier still governs unrestricted macro discovery.

Artifacts:

- `macro_assisted_subdag.py` — producer and work-accounted integration;
- `verify_macro_assisted_subdag.py` — independent proof and macro replay;
- `test_macro_assisted_subdag.py` — recovery, cap, accounting, and forgery tests;
- `MACRO_ASSISTED_SUBDAG.json` — serialized 4,097-node scan and certificates;
- `SYMBOLIC_SUFFIX_TEMPLATE_REPORT.md` — the suffix rule and its proof;
- `MACRO_ASSISTED_SUBDAG_REPORT.md` — this report.
