# RM(2,5) objective normalization audit

The quotient producer and independent replay build the objective over the 31 non-pinned singleton coordinates. Their saved value `31/5` is therefore a non-pin weight, not the total Hamming weight. Independent enumeration of the pinned RM(2,5) code gives total minimum weight `8` and non-pin minimum weight `7`. Adding the fixed pin contribution gives the equivalent total objective `36/5`, with ratio `10/9`; using the reduced objective gives ratio `35/31`. The old `40/31` comparison mixed these two conventions and is retired.

This is a normalization correction to the finite certificate record. It does not change the saved rational masses or quotient equations, and it does not imply anything about arbitrary SAT algorithms or P versus NP.
