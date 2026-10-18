# Independent check of the five-piece compression controls

The three saved controls at retained widths 3, 16, and 64 are correct. Fresh
greedy runs reproduce five output pieces and their exact saved certificates.
The compression checker replays each certificate against the original pieces.
The independently structured block-norm checker verifies each two-piece target
equals the original sum, using 84 closed-product certificates in total.

All original and target equations involve only the first three coordinates,
and all phases are empty. Checking this dependency restriction justifies
extending the independently evaluated eight-word table to the entire retained
domain at every width. The values are 2 at low word 000 and 1 at the other
seven low words. Thus the function has full support and two distinct absolute
values. A single nonzero real-affine quadratic piece has constant absolute
value on its affine support; it cannot represent this function. Zero pieces
cannot represent a nonzero function. The verified two-piece target therefore
proves the exact minimum is two.

This separates the frozen local greedy rules from a possible subgroup rewrite:
four original line pieces sum to the constant function, while the fifth piece
must remain. Whole-sum one-piece rejection is correct but does not discover
that subgroup. This is not a general compression, SAT, or complexity lower bound.

`python AFFINE_RECOGNITION_LIMITS_REVIEW.py` freshly checks 24 relevant truth
words, replays all three compression and norm certificates, and reruns the
greedy reducer three times. The resulting JSON records exact source and input
hashes and verifies they remained unchanged during the review. It records
fresh checks rather than relying solely on the original saved verdicts.
