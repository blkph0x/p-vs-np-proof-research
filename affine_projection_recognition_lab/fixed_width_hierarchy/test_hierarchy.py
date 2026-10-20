from copy import deepcopy
import json
import unittest

import chain
import verify


class FixedWidthHierarchyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.artifact = chain.build_artifact()

    def test_complete_independent_replay(self):
        checked = verify.verify_artifact(json.loads(json.dumps(self.artifact)))
        self.assertTrue(checked["valid"], checked)
        self.assertEqual(checked["relations"], 65814)
        self.assertEqual(checked["reduction_cases"], 1060)
        self.assertEqual(checked["cases_by_width"], {0: 4, 1: 512, 2: 512, 3: 32})
        self.assertEqual([r["maximum_depth"] for r in checked["chains"]], [1, 1, 3, 5, 7])
        self.assertEqual(checked["gadget_evaluations"], 344076)
        self.assertEqual(checked["source_evaluations"], 5286)

    def test_chain_coverage_and_mutations(self):
        for action in ("missing_width", "duplicate_width", "affinity", "depth", "chain", "convention"):
            forged = deepcopy(self.artifact)
            if action == "missing_width":
                forged["chains"].pop()
            elif action == "duplicate_width":
                forged["chains"][1] = forged["chains"][0]
            elif action == "affinity":
                forged["chains"][0]["affinity_bits"] = "11"  # Illegally accept empty.
            elif action == "depth":
                forged["chains"][2]["depths"][7] = 1  # Three points are nonaffine.
            elif action == "chain":
                forged["chains"][2]["canonical_chain"][1] = 15
            else:
                forged["convention"] = "empty_allowed"
            self.assertFalse(verify.verify_artifact(forged)["valid"], action)

    def test_source_inputs_not_assumed_nested(self):
        yes = {"nvars": 0, "clauses": []}
        no = {"nvars": 0, "clauses": [[]]}
        for sources, expected in (([no, yes, yes], False),
                                  ([yes, no, yes], True),
                                  ([yes, yes, no], False),
                                  ([yes, yes, yes], True)):
            record = chain.reduction_record(2, sources)
            checked = verify.verify_reduction(2, sources, record)
            self.assertTrue(checked["valid"], checked)
            self.assertIs(record["projection_affine"], expected)

    def test_original_variable_blocks_are_independent(self):
        sources = [{"nvars": 1, "clauses": [[1]]},
                   {"nvars": 1, "clauses": [[-1]]},
                   {"nvars": 1, "clauses": [[1]]}]
        record = chain.reduction_record(2, sources)
        self.assertEqual(record["projection"], 15)
        self.assertTrue(verify.verify_reduction(2, sources, record)["valid"])
        forged = deepcopy(record)
        forged["gadget"]["source_variables"][1] = forged["gadget"]["source_variables"][0]
        self.assertFalse(verify.verify_reduction(2, sources, forged)["valid"])

    def test_original_binding_and_rebound_hash(self):
        sources = [{"nvars": 0, "clauses": []} for _ in range(3)]
        record = chain.reduction_record(2, sources)
        changed = deepcopy(sources)
        changed[1]["clauses"] = [[]]
        rebound = deepcopy(record)
        rebound["gadget"]["sources"] = changed
        rebound["gadget"]["input_sha256"] = chain.source_digest(2, changed)
        self.assertFalse(verify.verify_reduction(2, changed, rebound)["valid"])
        self.assertFalse(verify.verify_reduction(2, changed, record)["valid"])
        rebound["gadget"] = chain.reduce_sat_prefix(2, changed)
        self.assertFalse(verify.verify_reduction(2, changed, rebound)["valid"])

    def test_reduction_claim_and_gadget_mutations(self):
        sources = [{"nvars": 0, "clauses": []} for _ in range(3)]
        record = chain.reduction_record(2, sources)
        for action in ("omit_clause", "literal", "extra", "model", "affine", "count",
                       "bool_integer", "prefix", "source_sat"):
            forged = deepcopy(record)
            if action == "omit_clause": forged["gadget"]["clauses"].pop(0)
            elif action == "literal": forged["gadget"]["clauses"][1][-1] *= -1
            elif action == "extra": forged["unknown"] = True
            elif action == "model": forged["projection"] = 7
            elif action == "affine": forged["projection_affine"] = False
            elif action == "count": forged["gadget_formula_evaluations"] -= 1
            elif action == "bool_integer": forged["gadget"]["visible_width"] = True
            elif action == "prefix": forged["longest_sat_prefix"] = 1
            else: forged["source_sat"][0] = False
            self.assertFalse(verify.verify_reduction(2, sources, forged)["valid"], action)

    def test_campaign_complete_source_order(self):
        for action in ("missing", "duplicate", "reordered"):
            forged = deepcopy(self.artifact)
            if action == "missing":
                forged["reductions"].pop()
            elif action == "duplicate":
                forged["reductions"][1] = forged["reductions"][0]
            else:
                forged["reductions"][0], forged["reductions"][1] = (
                    forged["reductions"][1], forged["reductions"][0])
            self.assertFalse(verify.verify_artifact(forged)["valid"], action)

    def test_empty_formula_clause_visible_width_and_unused_variables(self):
        for k in (0, 1, 2):
            for sat in (False, True):
                sources = [{"nvars": 2, "clauses": [] if sat else [[]]}
                           for _ in range(max(1, 2*k-1))]
                record = chain.reduction_record(k, sources)
                self.assertEqual(record["projection"],
                                 (1 << (1 << k))-1 if sat else 0)
                self.assertIs(record["projection_affine"], sat)
                self.assertTrue(verify.verify_reduction(k, sources, record)["valid"])

    def test_strict_inputs_and_enumeration_guard(self):
        for k in (True, -1, 5, 1.0, "1"):
            with self.assertRaises(ValueError):
                chain.canonical_chain(k)
        invalid = [
            {"nvars": True, "clauses": []}, {"nvars": 1, "clauses": [[0]]},
            {"nvars": 1, "clauses": [[2]]}, {"nvars": 1, "clauses": [[True]]},
            {"nvars": 1, "clauses": [[1.0]]}, {"nvars": 1, "clauses": [1]},
            {"nvars": 1, "clauses": [], "extra": 0},
        ]
        for spec in invalid:
            with self.assertRaises(ValueError):
                chain.reduce_sat_prefix(1, [spec])
            self.assertFalse(verify.verify_reduction(1, [spec], {})["valid"])
        with self.assertRaises(ValueError):
            chain.reduce_sat_prefix(2, [{"nvars": 0, "clauses": []}])
        with self.assertRaisesRegex(ValueError, "enumeration cap"):
            chain.reduction_record(4, [{"nvars": 1, "clauses": []} for _ in range(7)])

    def test_normalized_source_hash_scope(self):
        text = "exact α\nsecond line\n".encode("utf-8")
        self.assertEqual(verify.text_hash(text), verify.text_hash(text.replace(b"\n", b"\r\n")))
        self.assertEqual(verify.text_hash(text), verify.text_hash(text.replace(b"\n", b"\r")))
        self.assertNotEqual(verify.text_hash(text), verify.text_hash(text + b" "))
        self.assertNotEqual(verify.text_hash(text), verify.text_hash(b"\xef\xbb\xbf" + text))
        with self.assertRaises(UnicodeDecodeError):
            verify.text_hash(b"\xff")


if __name__ == "__main__":
    unittest.main()
