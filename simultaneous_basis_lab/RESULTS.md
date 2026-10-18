# Simultaneous basis results

Two exact parity obstructions over the complex numbers exclude a common invertible 2 by 2 basis for EQ3 with OR3, and for EQ3 with the slack factor [0,1,2,1], in the stated row/column convention. A separate product-type certificate excludes the other main symmetric Holant target: requiring transformed EQ3 to have product-type support forces a diagonal or anti-diagonal basis, under which both OR3 and SLACK3 still have three nonzero weight classes. The edge-specific certificate extends the obstruction to every degree-three equality/OR3 or equality/slack incidence network. This is a limitation of this basis route; P versus NP remains unresolved.

The saved certificate contains all eight five-equation parity systems, four integer Bezout identities, the rational symmetric-clause classification, the edge-specific EQ3/OR3 and EQ3/slack ±4 certificates, and the product-type case split. All eight per-edge flip patterns are replayed for both clauses. A standard-library verifier replays the identities and binds them to the original tensors. The accompanying direct proof classifies every admissible EQ3 basis and every rational symmetric ternary clause compatible with its parity; the program is not a formal proof assistant.

SymPy 1.14.0 independently returned the unit ideal for all eight systems. Those computations are corroboration, not the certificate of nonexistence.

Five explicit planar weighted graphs replay all 40 boundary entries. They verify shared Hadamard-basis EQ3/EQ3 and EQ3/NAE3 controls and individual OR3/slack3 transformations. Individual success does not supply a shared basis with EQ3.

All before/after source hashes agree; full inputs, exact fractions, polynomial terms, graph edges and timings are in RESULTS.json. The runner reloaded the saved JSON and replayed its proof identities and graph/tensor controls.

Run `python -m unittest -v test_basis.py` and `python run_experiments.py` from this directory. Tests include 200 seeded rational matrices checked by independent direct tensor summation, mutation rejection, all branch equations and the explicit graph signatures. No finite sample is used to infer nonexistence.

## Source hashes

- `basis.py`: `40edd2e54e7057c936d5ff86fb4fde1a2d38e51ccdf1fae37b23200367a84ef1`
- `test_basis.py`: `aebb2a18a0365547ae94d97db69be496c998a73342dca378389e09d84089b140`
- `run_experiments.py`: `fe74d24ff98388f5ab13c95540c2f288c577644b9db04aba94efa0f70f44c7f9`
- `THEOREM.md`: `6caebf538bcd1b5703be4f5e3a13fb019ed412f0d4450a2588a16e64bca53738`
