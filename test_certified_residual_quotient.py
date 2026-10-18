import unittest
import copy
from pathlib import Path
import sys

ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

import certified_residual_quotient as quotient


class TestCertifiedResidualQuotient(unittest.TestCase):
    def test_syntactic_merge(self):
        row = quotient.classify_pair(((1,),), ((1,),), 1)
        self.assertEqual(row["status"], "MERGED_SYNTACTIC")

    def test_resolution_certificate_merge(self):
        left = ((1,), (2,))
        right = ((1,), (2,), (1, 2))
        cert = quotient.build_equivalence_certificate(left, right)
        self.assertIsNotNone(cert)
        self.assertTrue(quotient.verify_equivalence_certificate(cert))
        row = quotient.classify_pair(left, right, 2, max_assignments=1,
                                     equivalence_certificate=cert)
        self.assertEqual(row["status"], "MERGED_PROOF")

    def test_forged_resolution_certificate_is_rejected(self):
        left = ((1,), (2,))
        right = ((1,), (2,), (1, 2))
        cert = quotient.build_equivalence_certificate(left, right)
        forged = copy.deepcopy(cert)
        forged["forward"]["obligations"][0]["proof"]["nodes"][-1]["clause"] = [1]
        self.assertTrue(quotient.verify_equivalence_certificate(cert))
        self.assertFalse(quotient.verify_equivalence_certificate(forged))

    def test_distinct_witness_is_one_sided(self):
        row = quotient.classify_pair(((1,),), ((2,),), 2, witness=(True, False))
        self.assertEqual(row["status"], "DISTINCT_WITNESS")

    def test_bounded_exact_distinction(self):
        row = quotient.classify_pair(((1,),), ((1, 2),), 2, max_assignments=4)
        self.assertEqual(row["status"], "DISTINCT_EXACT")

    def test_unknown_is_preserved_past_cap(self):
        row = quotient.classify_pair(((1,), (-1,)), (), 8, max_assignments=16)
        self.assertEqual(row["status"], "UNKNOWN")
        witness = quotient.classify_pair(((1,),), (), 8, max_assignments=16,
                                          witness=(False,) * 8)
        self.assertEqual(witness["status"], "DISTINCT_WITNESS")


if __name__ == "__main__":
    unittest.main()
