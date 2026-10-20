"""Independent geometry, exact replay, and adversarial nine-scope tests."""
from collections import Counter
from copy import deepcopy
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import unittest

from exact_lp_verify import model_digest, verify_solution
import review_rm2_nine_scope as review


HERE = Path(__file__).resolve().parent


def saved(directory):
    directory = HERE / directory
    return (json.loads((directory / "model.json").read_text(encoding="utf-8")),
            json.loads((directory / "candidate.json").read_text(encoding="utf-8")))


def activity(row, vector):
    return sum((Fraction(value) * vector[int(column)] for column, value in row.items()),
               Fraction())


def all_linear_three_flats():
    """Enumerate all 155 subspaces by independent triples, with no RM code API."""
    flats = set()
    for a, b, c in combinations(range(1, 32), 3):
        points = frozenset((0, a, b, c, a ^ b, a ^ c, b ^ c, a ^ b ^ c))
        if len(points) == 8:
            flats.add(points)
    return flats


class NineScopeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.details = review.rebuild_details()
        cls.model = cls.details["model"]
        cls.cut_model = review.rebuild_nine_point_cut_model()

    def assert_primal(self, vector):
        self.assertEqual(len(vector), len(self.model["objective"]))
        self.assertTrue(all(value >= 0 for value in vector))
        for index, (row, rhs) in enumerate(zip(self.model["rows"], self.model["rhs"])):
            self.assertEqual(activity(row, vector), Fraction(rhs), ("row", index))

    def test_exact_support_via_distinct_parity_characterization(self):
        atoms = self.details["allowed_atoms"]
        # The first eight points are an affine 3-flat; the ninth is outside.
        # This parity description is used only as a test of the independent
        # all-quadratic-coefficient evaluation in the checker.
        self.assertEqual(atoms, [atom for atom in range(512)
                                 if (atom & 255).bit_count() % 2 == 0])
        self.assertEqual(len(atoms), 256)
        self.assertEqual(review.pinned_projection_atoms((0,)), (1,))
        self.assertEqual(review.pinned_projection_atoms(()), (0,))

    def test_complete_moment_coverage_including_closures_outside_scope(self):
        metadata = self.details["moment_rows"]
        self.assertEqual(len(metadata), 362)
        masks = [item["mask"] for item in metadata]
        self.assertEqual(masks, sorted(set(masks)))
        for count in range(1, 5):
            for selected in combinations(range(9), count):
                self.assertIn(sum(1 << index for index in selected), masks)
        crossing = [item for item in metadata
                    if not set(item["closure"]).issubset(review.SCOPE)]
        self.assertEqual(len(crossing), 98)
        example = next(item for item in metadata if item["mask"] == 259)
        self.assertEqual(example["points"], [16, 17, 24])
        self.assertEqual(example["closure"], [16, 17, 24, 25])
        self.assertEqual(len(self.model["objective"]), 284)
        self.assertEqual(len(self.model["rows"]), 416)
        self.assertEqual(sum(len(row) for row in self.model["rows"]), 10089)

    def test_two_global_distributions_satisfy_every_row(self):
        allowed, var_for, _, _, _ = review._base()
        all_one = [Fraction(0)] * 284
        uniform = [Fraction(0)] * 284
        representatives = {}
        for (scope, atom), orbit in var_for.items():
            representatives.setdefault(orbit, (scope, atom))
        for orbit, (scope, atom) in representatives.items():
            all_one[orbit] = Fraction(atom == (1 << len(scope)) - 1)
            uniform[orbit] = Fraction(1, len(allowed[scope]))
        for index, atom in enumerate(self.details["allowed_atoms"]):
            all_one[28 + index] = Fraction(atom == 511)
            uniform[28 + index] = Fraction(1, 256)
        self.assert_primal(all_one)
        self.assert_primal(uniform)

    def test_actual_global_plane_distribution_has_reduced_weight_seven(self):
        flats = all_linear_three_flats()
        self.assertEqual(len(flats), 155)
        _, var_for, _, _, _ = review._base()
        representatives = {}
        for key, orbit in var_for.items():
            representatives.setdefault(orbit, key)
        vector = [Fraction(0)] * 284
        for orbit, (scope, atom) in representatives.items():
            count = sum(sum((point in flat) << index
                            for index, point in enumerate(scope)) == atom for flat in flats)
            vector[orbit] = Fraction(count, 155)
        counts = Counter(sum((point in flat) << index
                             for index, point in enumerate(review.SCOPE)) for flat in flats)
        for index, atom in enumerate(self.details["allowed_atoms"]):
            vector[28 + index] = Fraction(counts[atom], 155)
        self.assert_primal(vector)
        self.assertEqual(sum(Fraction(c) * x
                             for c, x in zip(self.model["objective"], vector)), 7)

    def test_nine_point_inequality_follows_from_all_moment_rows(self):
        combined = Counter()
        for item in self.details["moment_rows"]:
            multiplier = {1: 1, 2: -2, 3: 3}.get(item["mask"].bit_count(), 0)
            for column, coefficient in self.model["rows"][item["row_index"]].items():
                combined[int(column)] += multiplier * int(coefficient)
        cut = {int(column): int(value) for column, value in self.cut_model["rows"][-1].items()
               if int(column) != 28}
        for column in range(28):
            self.assertEqual(combined[column], -9 * cut.get(column, 0))
        for index, atom in enumerate(self.details["allowed_atoms"]):
            t = atom.bit_count()
            value = t * (t - 2) * (t - 3) // 2
            self.assertGreaterEqual(value, 0)
            self.assertEqual(combined[28 + index], value)

    def test_compact_dual_identity_from_original_atom_incidence(self):
        allowed, var_for, base_rows, base_rhs, objective = review._base()
        flat = tuple(range(16, 24))
        outside = 24
        groups = {}
        for atom in allowed[flat]:
            groups.setdefault(var_for[(flat, atom)], []).append(atom)
        orbits = sorted(groups)
        self.assertEqual(orbits, list(range(5, 11)))
        self.assertEqual(sum(map(len, groups.values())), 128)
        # b_i is the common per-atom mass with the outside bit equal to one;
        # s_i is its nonnegative complement within that base atom's mass.
        rows = [dict(row) for row in base_rows]
        rhs = list(base_rhs)
        for index, orbit in enumerate(orbits):
            rows.append({28 + index: 1, 34 + index: 1, orbit: -1})
            rhs.append(0)
        incidence = []
        for subset in ((), (16,), (16, 17), (16, 17, 18), (16, 17, 18, 19)):
            selected = sum(1 << flat.index(point) for point in subset)
            counts = [sum(atom & selected == selected for atom in groups[orbit])
                      for orbit in orbits]
            incidence.append(tuple(counts))
            row = Counter({28 + index: count for index, count in enumerate(counts) if count})
            moment = review.base_moment((outside,) + subset)["coefficients"]
            for column, count in moment.items():
                row[column] -= count
            rows.append({column: value for column, value in row.items() if value})
            rhs.append(0)
        # These lists are outputs being checked, never inputs to construction.
        self.assertEqual(incidence, [
            (1, 28, 14, 56, 28, 1),
            (0, 7, 7, 28, 21, 1),
            (0, 1, 3, 12, 15, 1),
            (0, 0, 1, 4, 10, 1),
            (0, 0, 1, 0, 6, 1),
        ])
        self.assertEqual(len(rows), 64)
        multipliers = {
            1: 1296, 3: -1764, 5: 252, 7: 279, 12: -468, 13: -2034,
            14: -2160, 15: -762, 17: -1296, 18: -5022, 19: -8424,
            20: -4530, 24: 252, 25: 504, 31: 279, 56: -952, 58: -328,
            60: 252, 61: -1764, 62: 1624,
        }

        def transpose_product(matrix):
            vector = [Fraction(0)] * 40
            for row_index, multiplier in multipliers.items():
                for column, coefficient in matrix[row_index].items():
                    vector[column] += multiplier * coefficient
            return vector

        transposed = transpose_product(rows)
        expected = {27: 279, 2: -672, 30: -1904, 31: -8568, 32: -4928,
                    33: -216, 37: -952, 39: -328}
        self.assertEqual({i: value for i, value in enumerate(transposed) if value}, expected)
        self.assertEqual(sum(value * rhs[index] for index, value in multipliers.items()), 63)
        self.assertEqual(review.base_moment((outside,))["coefficients"], {27: 1})
        costs = list(objective) + [Fraction(0)] * 12
        reduced = [cost - value / 9 for cost, value in zip(costs, transposed)]
        self.assertTrue(all(value >= 0 for value in reduced))
        self.assertEqual(Fraction(63, 9), 7)
        # A mistaken point-incidence count must change the exact identity.
        corrupted = [dict(row) for row in rows]
        corrupted[60][29] += 1
        self.assertNotEqual(transpose_product(corrupted), transposed)

    def test_intermediate_cut_is_geometry_bound_with_correct_dual_slack_sign(self):
        model, certificate = saved("RM2_NINE_POINT_CUT_CONTROL")
        self.assertEqual(model, self.cut_model)
        checked = review.replay_nine_point_cut(model, certificate)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["reduced_objective"], "1147/184")
        self.assertEqual(certificate["dual"][-1], "217/184")
        self.assertEqual(model["rows"][-1]["28"], "-1")
        bad = deepcopy(certificate)
        bad["dual"][-1] = "-217/184"
        self.assertFalse(review.replay_nine_point_cut(model, bad)["valid"])

    def test_intermediate_mixture_cannot_extend_to_the_nine_scope(self):
        model, certificate = saved("RM2_NINE_POINT_CUT_CONTROL")
        vector = [Fraction(value) for value in certificate["primal"]]
        self.assertEqual(activity(model["rows"][-1], vector), 0)
        p = review.base_moment((1,))["coefficients"]
        q = review.base_moment((1, 2))["coefficients"]
        r = review.base_moment((1, 2, 4))["coefficients"]
        value = lambda coefficients: sum(vector[column] * count
                                         for column, count in coefficients.items())
        self.assertEqual(value(p) - 8 * value(q) + 28 * value(r), 0)
        plane = review.base_moment((16, 17, 18, 19))["coefficients"]
        self.assertEqual(value(plane), Fraction(1, 736))
        zeros = [t for t in range(10) if t * (t - 2) * (t - 3) == 0]
        self.assertEqual(zeros, [0, 2, 3])
        # Hence E[f(T)]=0 would force T<=3, contradicting this plane's positive
        # all-one event. This is an obstruction, not a full-L9 certificate.

    def test_saved_full_extension_certificate_replays(self):
        model, certificate = saved("RM2_NINE_SCOPE_DISCOVERY")
        self.assertEqual(model, self.model)
        checked = review.replay_nine_scope(model, certificate)
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["reduced_objective"], "7")
        self.assertEqual(checked["total_objective"], "8")
        self.assertEqual(checked["full_L9_upper_bound"], "NOT_ESTABLISHED_BY_THIS_CERTIFICATE")

    def test_false_vectors_and_claims_are_rejected(self):
        model, certificate = saved("RM2_NINE_SCOPE_DISCOVERY")
        mutations = []
        for key, value in (
            ("primal", certificate["primal"][:-1]),
            ("dual", ["0"] * len(certificate["dual"])),
            ("claimed_objective", "8"),
            ("model_sha256", "0" * 64),
        ):
            bad = deepcopy(certificate)
            bad[key] = value
            mutations.append(bad)
        bad = deepcopy(certificate)
        index = next(i for i, value in enumerate(bad["primal"]) if Fraction(value) > 0)
        bad["primal"][index] = str(-Fraction(bad["primal"][index]))
        mutations.append(bad)
        bad = deepcopy(certificate)
        bad["primal"][0] = 0.0
        mutations.append(bad)
        for bad in mutations:
            with self.subTest(mutation=bad):
                self.assertFalse(review.replay_nine_scope(model, bad)["valid"])

    def test_rebound_model_mutations_cannot_replace_original_source(self):
        model, certificate = saved("RM2_NINE_SCOPE_DISCOVERY")
        mutations = []
        crossing = next(item for item in self.details["moment_rows"]
                        if not set(item["closure"]).issubset(review.SCOPE))["row_index"]
        missing = deepcopy(model)
        missing["rows"].pop(crossing)
        missing["rhs"].pop(crossing)
        missing["row_ids"] = [f"r{i:06d}" for i in range(len(missing["rows"]))]
        mutations.append(missing)
        for field, value in (("name", "unrelated_lp"), ("objective_offset", "0")):
            bad = deepcopy(model)
            bad[field] = value
            mutations.append(bad)
        bad = deepcopy(model)
        bad["rows"][53] = {column: str(-int(value))
                            for column, value in bad["rows"][53].items()}
        bad["rhs"][53] = "-1"
        mutations.append(bad)
        bad = deepcopy(model)
        for row in bad["rows"]:
            first, second = row.pop("28", None), row.pop("29", None)
            if first is not None:
                row["29"] = first
            if second is not None:
                row["28"] = second
        mutations.append(bad)
        for bad in mutations:
            proof = deepcopy(certificate)
            proof["model_sha256"] = model_digest(bad)
            checked = review.replay_nine_scope(bad, proof)
            self.assertFalse(checked["valid"])
            self.assertIn("model differs from independently rebuilt", checked["errors"][0])
        # A changed reporting offset really can be a valid generic LP proof:
        # source reconstruction supplies the additional binding obligation.
        shifted = deepcopy(model)
        shifted["objective_offset"] = "0"
        proof = deepcopy(certificate)
        proof["model_sha256"] = model_digest(shifted)
        self.assertTrue(verify_solution(shifted, proof)["valid"])

    def test_reconstruction_is_fresh_and_input_types_are_strict(self):
        changed = review.rebuild_model()
        changed["rows"][0].clear()
        self.assertEqual(review.rebuild_model(), self.model)
        for points in ([True], [1, 1], [-1], [32], [1.0], list(range(10)), {1, 2}):
            with self.subTest(points=points), self.assertRaises(ValueError):
                review.pinned_projection_atoms(points)
        for bad in (None, {}, {"schema": True}):
            self.assertFalse(review.replay_nine_scope(bad, {})["valid"])


if __name__ == "__main__":
    unittest.main()
