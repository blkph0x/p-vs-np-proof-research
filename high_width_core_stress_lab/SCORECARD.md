# Proof / computation / open-problem audit

| Result | Evidence type | Universal? |
|---|---|---|
| M(K_t) internally 4-connected, t>=5 | Elementary proof in THEOREMS.md | Yes for named graphic family |
| pw(M(K_t)) = t-2 | Elementary lower/upper proof | Yes for named graphic family |
| Cut-code distance=t-1, cycle-code distance=3 | Graph equivalence + native exact algorithms | Yes for K_t |
| Random 18..26 sample internal4 | Exhaustive C++ GF(2) rank enumeration | Finite samples only |
| Random 28 sample trellis >=8 | Exhaustive balanced cuts | Finite sample only; internal4 unverified |
| Existence of codes with pw=Omega(n) | Probabilistic theorem | Existential, no minweight hardness |
| Heuristic trellis DP minweights | Crosschecked against 2^dimension enumeration | Finite instances only |
| General minimum-distance NP-complete | Vardy 1997 | Hardness of unrestricted family |
| Hard average-case random-code min distance | Unknown here | Not proved |
| P=NP / universal polynomial merger | Unknown | Not proved |
