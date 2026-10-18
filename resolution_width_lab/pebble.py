"""Boolean existential pebble-game closure for resolution-width certificates.

Atserias and Dalmau's width characterization identifies a resolution
refutation of width ``w`` with Spoiler winning the Boolean existential
``(w + 1)``-pebble game.  A position is a partial assignment that does not
falsify an input clause.  The greatest family closed under projections and
the Duplicator extension rule is computed exactly; an empty family is a
finite Spoiler certificate, while a nonempty fixed point is a Duplicator
certificate.

The implementation uses two ``n``-bit masks per position.  The high bits of
the integer key are the assigned-variable mask and the low bits are the mask
of variables assigned True.  This is only a representation change: the game
rules are checked on the same partial assignments as the tuple definition.
"""
from __future__ import annotations

from hashlib import sha256
from itertools import combinations
import json
from time import perf_counter

from resolution import normalize_clause


def _digest(codes):
    """Return a stable digest for a set of encoded positions."""
    payload = json.dumps(sorted(codes), separators=(",", ":")).encode()
    return sha256(payload).hexdigest()


class BooleanPebbleGame:
    """Compute the exact Boolean existential pebble-game fixed point."""

    def __init__(self, nvars, clauses, pebbles):
        if type(nvars) is not int or nvars < 0:
            raise ValueError("nvars must be a nonnegative integer")
        if type(pebbles) is not int or pebbles < 0:
            raise ValueError("pebbles must be a nonnegative integer")
        self.nvars = nvars
        # Keep the requested pebble count in the result even when it exceeds
        # the number of variables; the extra pebbles are simply never used.
        self.pebbles = pebbles
        self.clauses = []
        for raw in clauses:
            clause = normalize_clause(raw)
            if clause is None:
                continue
            if any(abs(lit) > nvars for lit in clause):
                raise ValueError("literal outside declared variable range")
            self.clauses.append(clause)
        self._clause_masks = []
        for clause in self.clauses:
            positive = negative = 0
            for literal in clause:
                bit = 1 << (abs(literal) - 1)
                if literal > 0:
                    positive |= bit
                else:
                    negative |= bit
            self._clause_masks.append((positive, negative))

    def _initial_positions(self):
        """Enumerate every non-falsifying partial assignment up to the cap."""
        positions = set()
        for domain_size in range(min(self.pebbles, self.nvars) + 1):
            for variables in combinations(range(self.nvars), domain_size):
                domain = sum(1 << variable for variable in variables)
                true_mask = domain
                while True:
                    falsifies = False
                    for positive, negative in self._clause_masks:
                        if ((positive | negative) & ~domain) == 0 and \
                                true_mask & positive == 0 and \
                                true_mask & negative == negative:
                            falsifies = True
                            break
                    if not falsifies:
                        positions.add((domain << self.nvars) | true_mask)
                    if true_mask == 0:
                        break
                    true_mask = (true_mask - 1) & domain
        return positions

    def solve(self):
        """Return the fixed point and an auditable elimination trace."""
        started = perf_counter()
        active = self._initial_positions()
        initial_count = len(active)
        all_variables = (1 << self.nvars) - 1
        rounds = []

        while True:
            removed = []
            projection_witnesses = 0
            extension_witnesses = 0
            for code in active:
                domain = code >> self.nvars
                true_mask = code & all_variables
                failed = False

                # A strategy is closed under every projection.
                assigned = domain
                while assigned:
                    bit = assigned & -assigned
                    assigned -= bit
                    projected = ((domain ^ bit) << self.nvars) | (true_mask & ~bit)
                    if projected not in active:
                        failed = True
                        projection_witnesses += 1
                        break
                if failed:
                    removed.append(code)
                    continue

                # With a free pebble, Duplicator must answer every new
                # variable with at least one of its two truth values.
                if domain.bit_count() < self.pebbles:
                    missing = all_variables ^ domain
                    while missing:
                        bit = missing & -missing
                        missing -= bit
                        child_domain = domain | bit
                        false_child = (child_domain << self.nvars) | true_mask
                        true_child = (child_domain << self.nvars) | (true_mask | bit)
                        if false_child not in active and true_child not in active:
                            failed = True
                            extension_witnesses += 1
                            break
                if failed:
                    removed.append(code)

            if not removed:
                break
            for code in removed:
                active.remove(code)
            rounds.append({
                "removed": len(removed),
                "projection_witnesses": projection_witnesses,
                "extension_witnesses": extension_witnesses,
                "remaining": len(active),
            })

        final_by_domain = {}
        for code in active:
            domain_size = (code >> self.nvars).bit_count()
            final_by_domain[str(domain_size)] = final_by_domain.get(str(domain_size), 0) + 1
        status = "DUPLICATOR_WINS" if active else "SPOILER_WINS"
        return {
            "status": status,
            "reason": "FIXED_POINT" if active else "EMPTY_FIXED_POINT",
            "nvars": self.nvars,
            "pebbles": self.pebbles,
            "clause_count": len(self.clauses),
            "initial_states": initial_count,
            "final_states": len(active),
            "final_states_by_domain": final_by_domain,
            "rounds": rounds,
            "round_count": len(rounds),
            "surviving_state_sha256": _digest(active),
            "elapsed_seconds": perf_counter() - started,
        }


__all__ = ["BooleanPebbleGame"]
