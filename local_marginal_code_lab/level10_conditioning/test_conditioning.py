"""Original-geometry, exact algebra, source-binding and mutation controls."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
from pathlib import Path
import hashlib
import json
import unittest

import replay

HERE = Path(__file__).resolve().parent


def kernels(codimension):
    if codimension == 1:
        constraints = [(row,) for row in range(1, 64)]
    elif codimension == 2:
        constraints = sorted({tuple(sorted((a, b, a ^ b)))
                              for a, b in combinations(range(1, 64), 2)})
    else:
        raise ValueError("control supports only codimension1 or2")
    return [sum(1 << point for point in range(64)
                if all((row & point).bit_count() % 2 == 0 for row in rows))
            for rows in constraints]


def word_values(words):
    """Direct original global-word oracle; no LP or symbolic row evaluation."""
    n = len(words)
    answer = {"one": Fraction(1)}
    for name, points in (("p", (1,)), ("q", (1, 2)), ("r", (1, 2, 4)),
                         ("h", (1, 2, 4, 7)), ("v", (1, 2, 4, 8))):
        answer[name] = Fraction(sum(all(word >> point & 1 for point in points)
                                    for word in words), n)
    pin_counts = Counter(word & 255 for word in words)
    pin_groups = [[] for _ in range(5)]
    for atom in range(1, 256, 2):
        selected = [point for point in range(1, 8) if atom >> point & 1]
        size = len(selected)
        if size == 1:
            kind = 0
        elif size == 3:
            kind = 1 if selected[0] ^ selected[1] ^ selected[2] == 0 else 2
        elif size == 5:
            kind = 3
        elif size == 7:
            kind = 4
        else:
            continue
        pin_groups[kind].append(atom)
    for kind, atoms in enumerate(pin_groups):
        counts = {pin_counts[atom] for atom in atoms}
        if len(counts) != 1:
            raise ValueError("global control lacks pinned-flat orbit invariance")
        answer[f"z{kind}"] = Fraction(counts.pop(), n)
    counts = [Counter(), Counter(), Counter()]
    for word in words:
        atom = (word >> 16) & 255
        counts[0][atom] += 1
        if word >> 24 & 1:
            counts[1][atom] += 1
            if word >> 32 & 1:
                counts[2][atom] += 1
    groups = {key: [] for key in ("0", "2", "P", "N", "6", "8")}
    for atom in range(256):
        size = atom.bit_count()
        if size % 2:
            continue
        if size == 4:
            total = 0
            for point in range(8):
                if atom >> point & 1:
                    total ^= 16 + point
            kind = "P" if total == 0 else "N"
        else:
            kind = str(size)
        groups[kind].append(atom)
    for position, (kind, atoms) in enumerate(groups.items()):
        for prefix, source in zip((f"z{5+position}", "b" + kind, "g" + kind), counts):
            masses = {source[atom] for atom in atoms}
            if len(masses) != 1:
                raise ValueError("global control lacks affine-flat orbit invariance")
            answer[prefix] = Fraction(masses.pop(), n)
    return answer


class ConditioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.models = {}
        cls.candidates = {}
        for label in ("scalar", "identity"):
            cls.models[label] = json.loads((HERE / "exact_run" / label / "model.json").read_text())
            cls.candidates[label] = json.loads((HERE / "exact_run" / label / "candidate.json").read_text())
        # Rebuild once; tests must not replace original-source binding with a digest.
        replay.rebuild_model(True)
        replay.rebuild_model(False)

    def test_saved_exact_optima(self):
        for label, value in (("scalar", "1953/8369"), ("identity", "5/21")):
            checked = replay.replay(self.models[label], self.candidates[label], label == "identity")
            self.assertTrue(checked["valid"], checked)
            self.assertEqual(checked["reduced_objective"], value)
            self.assertEqual(checked["objective_offset"], "0")
        self.assertLess(Fraction(3843, 16675), Fraction(1953, 8369))
        self.assertLess(Fraction(1953, 8369), Fraction(5, 21))

    def test_elementary_eight_term_identity_and_mutations(self):
        self.assertEqual(replay.verify_elementary_identity()["terms"], 8)
        for position in (0, 8, 19):
            changed = list(replay.MULTIPLIERS)
            changed[position] += 1
            with self.assertRaisesRegex(ValueError, "identity mismatch"):
                replay.verify_elementary_identity(changed)
        with self.assertRaises(ValueError):
            replay.verify_elementary_identity([True] * 20)

    def test_conditional_atom_maps(self):
        checked = replay.check_atom_maps()
        self.assertEqual(checked["independent_triples"], 28)
        self.assertEqual(checked["even_H_atoms"], 128)
        self.assertEqual(checked["original_scope_size"], checked["conditional_scope_size"] + 1)

    def test_actual_global_codimension_two_upper_and_zero_slacks(self):
        words = kernels(2)
        self.assertEqual(len(words), 651)
        self.assertEqual(len(set(words)), 651)
        self.assertTrue(all(word & 1 and word.bit_count() == 16 for word in words))
        values = word_values(words)
        self.assertEqual(values["p"], Fraction(5, 21))
        self.assertEqual(values["q"], Fraction(5, 93))
        self.assertEqual(values["r"], Fraction(7, 651))
        self.assertEqual(values["v"], Fraction(1, 651))
        for equation in replay.elementary_equations():
            self.assertEqual(sum(coef * values[name] for name, coef in equation.items()), 0)
        for name in ("z2", "z3", "gP", "gN", "g8"):
            self.assertEqual(values[name], 0)
        self.assertEqual(values["b6"] - values["g6"], 0)
        self.assertEqual(values["b8"] - values["g8"], 0)
        self.assertEqual(values["z8"] - 2 * values["bN"] + values["gN"], 0)

    def test_nontight_global_controls_satisfy_every_incidence(self):
        for words in (kernels(1), [(1 << 64) - 1]):
            values = word_values(words)
            for equation in replay.elementary_equations():
                self.assertEqual(sum(coef * values[name] for name, coef in equation.items()), 0)
            self.assertGreater(values["p"], Fraction(5, 21))
            self.assertGreater(5481 * values["p"] - 1305, 0)

    def test_source_mutations_rejected_after_digest_rebinding(self):
        mutations = []
        removed = deepcopy(self.models["identity"])
        removed["rows"].pop()
        removed["rhs"].pop()
        removed["row_ids"].pop()
        mutations.append(removed)
        wrong_sign = deepcopy(self.models["identity"])
        wrong_sign["rows"][-1]["8"] = "672"
        mutations.append(wrong_sign)
        wrong_offset = deepcopy(self.models["identity"])
        wrong_offset["objective_offset"] = "1"
        mutations.append(wrong_offset)
        changed_old_row = deepcopy(self.models["identity"])
        key = next(iter(changed_old_row["rows"][0]))
        changed_old_row["rows"][0][key] = str(Fraction(changed_old_row["rows"][0][key]) + 1)
        mutations.append(changed_old_row)
        for changed in mutations:
            candidate = deepcopy(self.candidates["identity"])
            candidate["model_sha256"] = replay.model_digest(changed)
            checked = replay.replay(changed, candidate)
            self.assertFalse(checked["valid"])
            self.assertEqual(checked["status"], "INVALID")

    def test_primal_dual_objective_and_type_mutations(self):
        for field, index, value in (("primal", 27, "1/4"),
                                    ("primal", 0, "-1"),
                                    ("dual", 80, "0"),
                                    ("primal", 0, 0.0),
                                    ("dual", 0, True)):
            candidate = deepcopy(self.candidates["identity"])
            candidate[field][index] = value
            self.assertFalse(replay.replay(self.models["identity"], candidate)["valid"])
        candidate = deepcopy(self.candidates["identity"])
        candidate["claimed_objective"] = "1/5"
        self.assertFalse(replay.replay(self.models["identity"], candidate)["valid"])

    def test_saved_matrix_dual_identity_and_unused_old_cut(self):
        model, candidate = self.models["identity"], self.candidates["identity"]
        saved = json.loads((HERE / "exact_run/identity/integer-identity.json").read_text())
        summed = Counter()
        rhs = Fraction()
        for index, multiplier in saved["equality_row_multipliers"].items():
            row_index = int(index)
            rhs += multiplier * Fraction(model["rhs"][row_index])
            for col, coefficient in model["rows"][row_index].items():
                summed[int(col)] += multiplier * Fraction(coefficient)
        self.assertEqual(rhs, saved["constant"])
        for col in range(len(model["objective"])):
            wanted = saved["scale"] * Fraction(model["objective"][col])
            wanted -= saved["nonnegative_coefficients"].get(str(col), 0)
            self.assertEqual(summed[col], wanted)
        self.assertEqual(Fraction(candidate["dual"][64]), 0)
        self.assertTrue(all(value > 0 for value in saved["nonnegative_coefficients"].values()))

    def test_discovery_provenance_and_artifact_hashes(self):
        report = json.loads((HERE / "exact_run/RESULTS.json").read_text())
        self.assertTrue(report["sources_unchanged"])
        self.assertEqual(report["source_sha256_lf"], report["source_after_sha256_lf"])
        for name, expected in report["source_sha256_lf"].items():
            actual = hashlib.sha256((HERE.parent / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
            self.assertEqual(actual, expected, name)
        for label, entry in report["results"].items():
            for name, expected in entry["artifact_sha256"].items():
                actual = hashlib.sha256((HERE / "exact_run" / label / name).read_bytes()).hexdigest()
                self.assertEqual(actual, expected, label + "/" + name)


if __name__ == "__main__":
    unittest.main()
