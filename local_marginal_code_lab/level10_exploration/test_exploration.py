"""Exact source reconstruction, semantic controls, and saved-certificate replay."""
from collections import Counter
from fractions import Fraction
from itertools import product
from pathlib import Path
import copy
import hashlib
import json
import unittest

import investigate_mixed_cut as mixed
import investigate_ten_scope as ten
import investigate_double_external as double
import investigate_compact_combined as compact
import review_level10 as independent

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text())


def residuals(model, primal):
    primal = list(map(Fraction, primal))
    return [sum(Fraction(coefficient) * primal[int(column)]
                for column, coefficient in row.items()) - Fraction(target)
            for row, target in zip(model["rows"], model["rhs"])]


class ExplorationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rebuilt = {
            "mixed_cut_run/nine_control": mixed.make_model(False)[0],
            "mixed_cut_run/ten_cut": mixed.make_model(True)[0],
            "ten_scope_run/selected_ten_scope": ten.build()[0],
            "double_external_run/compact": double.extend(*mixed.make_model(True))[0],
            "double_external_run/combined": double.extend(*ten.build())[0],
            "compact_combined_run/compact_combined": compact.build()[0],
        }

    def test_all_six_models_source_bind_and_exact_replay(self):
        expected = ["7/31", "92/407", "11641/50713", "3843/16675", "3843/16627", "3843/16627"]
        for (relative, rebuilt), optimum in zip(self.rebuilt.items(), expected):
            directory = HERE / relative
            model, candidate = read(directory / "model.json"), read(directory / "candidate.json")
            self.assertEqual(model, rebuilt, relative)
            checked = mixed.verify_solution(model, candidate)
            self.assertTrue(checked["valid"], (relative, checked))
            self.assertEqual(candidate["claimed_objective"], optimum)
            self.assertFalse(any(residuals(model, candidate["primal"])))

    def test_source_hashes_are_current(self):
        for run in ("mixed_cut_run", "ten_scope_run", "double_external_run", "compact_combined_run"):
            report = read(HERE / run / "RESULTS.json")
            self.assertIs(report["sources_unchanged"], True)
            self.assertEqual(report["source_sha256_lf"], report["source_after_sha256_lf"])
            for relative, expected in report["source_sha256_lf"].items():
                actual = hashlib.sha256((HERE.parent / relative).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                self.assertEqual(actual, expected, relative)

    def test_integer_dual_identities_are_exact_columnwise(self):
        for relative, model in self.rebuilt.items():
            identity = read(HERE / relative / "integer-identity.json")
            combination = Counter()
            constant = Fraction()
            for row_index, multiplier in identity["equality_row_multipliers"].items():
                index = int(row_index)
                constant += Fraction(model["rhs"][index]) * multiplier
                for column, value in model["rows"][index].items():
                    combination[column] += Fraction(value) * multiplier
            self.assertEqual(constant, identity["constant"])
            for i, coefficient in enumerate(model["objective"]):
                reduced = identity["scale"] * Fraction(coefficient) - combination[str(i)]
                self.assertEqual(reduced, identity["nonnegative_coefficients"].get(str(i), 0))
                self.assertGreaterEqual(reduced, 0)

    def test_model_and_certificate_mutations_are_not_silently_accepted(self):
        directory = HERE / "double_external_run/compact"
        model, certificate = read(directory / "model.json"), read(directory / "candidate.json")
        bad_model = copy.deepcopy(model)
        bad_model["rows"][-1] = {}
        self.assertNotEqual(bad_model, self.rebuilt["double_external_run/compact"])
        bad = copy.deepcopy(certificate)
        bad["primal"][27] = "0"
        self.assertFalse(mixed.verify_solution(model, bad)["valid"])
        bad = copy.deepcopy(certificate)
        bad["dual"] = ["0"] * len(bad["dual"])
        self.assertFalse(mixed.verify_solution(model, bad)["valid"])
        bad = copy.deepcopy(certificate)
        bad["claimed_objective"] = "5/21"
        self.assertFalse(mixed.verify_solution(model, bad)["valid"])

    def test_independent_original_scope_rebuild_and_source_rebound_mutations(self):
        directory = HERE / "compact_combined_run/compact_combined"
        model, certificate = read(directory / "model.json"), read(directory / "candidate.json")
        self.assertEqual(independent.rebuild_model(), model)
        self.assertTrue(independent.replay(model, certificate)["valid"])
        identity = read(directory / "integer-identity.json")
        self.assertTrue(independent.verify_short_identity(model, identity)["valid"])
        changed = copy.deepcopy(model)
        changed["rows"][64]["40"] = "1"
        rebound = copy.deepcopy(certificate)
        rebound["model_sha256"] = mixed.model_digest(changed)
        self.assertFalse(independent.replay(changed, rebound)["valid"])
        changed = copy.deepcopy(model)
        changed["rows"].pop()
        changed["rhs"].pop()
        changed["row_ids"].pop()
        rebound = copy.deepcopy(certificate)
        rebound["dual"].pop()
        rebound["model_sha256"] = mixed.model_digest(changed)
        self.assertFalse(independent.replay(changed, rebound)["valid"])
        changed_identity = copy.deepcopy(identity)
        changed_identity["equality_row_multipliers"]["103"] += 1
        with self.assertRaises(ValueError):
            independent.verify_short_identity(model, changed_identity)

    def test_actual_d6_distribution_controls(self):
        paths = (
            ("ten_scope_run/d6-feasible-control.json", "ten_scope_run/selected_ten_scope"),
            ("double_external_run/compact-d6-control.json", "double_external_run/compact"),
            ("double_external_run/combined-d6-control.json", "double_external_run/combined"),
        )
        for point_path, model_path in paths:
            point = read(HERE / point_path)
            self.assertEqual(point["kernel_count"], 651)
            self.assertEqual(point["singleton_probability"], "5/21")
            self.assertTrue(all(Fraction(x) >= 0 for x in point["primal"]))
            self.assertFalse(any(residuals(self.rebuilt[model_path], point["primal"])))

    def test_complete_quadratic_projection_by_all_polynomial_coefficients(self):
        atoms, rows = ten.projection_atoms(ten.SCOPE)
        # Independently visit all 2^21 polynomials in Gray-code order.
        word = (1 << 10) - 1
        direct = {word}
        for index in range(1, 1 << 21):
            word ^= rows[(index & -index).bit_length() - 1]
            direct.add(word)
        self.assertEqual(set(atoms), direct)
        inside_positions = sum(1 << ten.SCOPE.index(point) for point in compact.INSIDE)
        expected = {word for word in range(1024) if (word & inside_positions).bit_count() % 2}
        self.assertEqual(direct, expected)
        self.assertEqual(len(direct), 512)

    def test_linear_coordinate_maps_preserve_every_relation(self):
        metadata = read(HERE / "ten_scope_run/selected_ten_scope/model-details.json")
        self.assertEqual(len(metadata["moment_rows"]), 435)
        for row in metadata["moment_rows"]:
            points, encoded = row["points"], row["encoded_points"]
            self.assertEqual(len(points), len(encoded))
            for mask in range(1 << len(points)):
                left = right = 0
                for i, (point, image) in enumerate(zip(points, encoded)):
                    if mask >> i & 1:
                        left ^= point
                        right ^= image
                self.assertEqual(left == 0, right == 0)
            self.assertLessEqual(len(ten.affine_closure(points)), 8)

    def test_twenty_atom_orbits_and_raw_expansion(self):
        groups = {i: [] for i in range(5)}
        for mask in range(128):
            if mask.bit_count() % 2:
                groups[compact.atom_type(mask)].append(mask)
        self.assertEqual([len(groups[i]) for i in range(5)], [7, 7, 28, 21, 1])
        automorphisms = []
        for a, b, c in product(range(1, 8), repeat=3):
            images = {0, a, b, c, a ^ b, a ^ c, b ^ c, a ^ b ^ c}
            if len(images) == 8:
                automorphisms.append((a, b, c))
        self.assertEqual(len(automorphisms), 168)
        for i, members in groups.items():
            representative = members[0]
            orbit = set()
            for images in automorphisms:
                image_mask = 0
                for position in range(7):
                    if representative >> position & 1:
                        point, image = position + 1, 0
                        for bit, basis_image in enumerate(images):
                            if point >> bit & 1:
                                image ^= basis_image
                        image_mask |= 1 << (image - 1)
                orbit.add(image_mask)
            self.assertEqual(orbit, set(members))
        point = read(HERE / "compact_combined_run/raw-expansion.json")
        self.assertEqual(point["singleton_probability"], "3843/16627")
        self.assertFalse(any(residuals(self.rebuilt["double_external_run/combined"], point["primal"])))

    def test_short_identity_from_elementary_incidence_equations(self):
        # This uses the written equations themselves, not any saved LP matrix.
        import sympy as s
        z = s.symbols("z0:11")
        p, q, r, h, v = s.symbols("p q r h v")
        b = s.symbols("b0 b2 bP bN b6 b8")
        g = s.symbols("g0 g2 gP gN g6 g8")
        equations = [
            7*z[0]+7*z[1]+28*z[2]+21*z[3]+z[4]-1,
            p-z[0]-3*z[1]-12*z[2]-15*z[3]-z[4],
            q-z[1]-4*z[2]-10*z[3]-z[4], r-z[2]-6*z[3]-z[4], h-3*z[3]-z[4],
            z[5]+28*z[6]+14*z[7]+56*z[8]+28*z[9]+z[10]-1,
            p-7*z[6]-7*z[7]-28*z[8]-21*z[9]-z[10],
            q-z[6]-3*z[7]-12*z[8]-15*z[9]-z[10],
            r-z[7]-4*z[8]-10*z[9]-z[10], h-z[7]-6*z[9]-z[10],
            v-z[8]-6*z[9]-z[10],
            p-b[0]-28*b[1]-14*b[2]-56*b[3]-28*b[4]-b[5],
            q-7*b[1]-7*b[2]-28*b[3]-21*b[4]-b[5],
            r-b[1]-3*b[2]-12*b[3]-15*b[4]-b[5],
            v-b[2]-4*b[3]-10*b[4]-b[5],
            3*z[9]+z[10]-b[2]-6*b[4]-b[5],
            q-g[0]-28*g[1]-14*g[2]-56*g[3]-28*g[4]-g[5],
            r-7*g[1]-7*g[2]-28*g[3]-21*g[4]-g[5],
            v-g[1]-3*g[2]-12*g[3]-15*g[4]-g[5],
        ]
        multipliers = [3843,26901,-53802,40992,-10248,0,-10226,71582,-153412,
                       10248,288288,0,-17780,124460,-372568,147072,0,-12040,84280]
        rhs = (40992*z[2]+23424*b[2]+168560*g[2]+426944*g[3]+336496*g[4]+12832*g[5]
               +247296*(z[8]-2*b[3]+g[3])+674864*(z[9]-2*b[4]+g[4])
               +59408*(z[10]-2*b[5]+g[5]))
        target = 16675*p-3843-rhs
        combination = sum(a*b for a, b in zip(multipliers, equations))
        self.assertEqual(s.expand(target-combination), 0)
        self.assertNotEqual(s.expand(target-combination+g[4]), 0)
        self.assertNotEqual(s.expand(target-combination+1), 0)
        self.assertGreater(Fraction(3843,16675), Fraction(92,407))
        self.assertGreater(Fraction(3843,16627), Fraction(3843,16675))
        self.assertLess(Fraction(3843,16627), Fraction(5,21))


if __name__ == "__main__":
    unittest.main()
