import copy
import json
from pathlib import Path
import unittest
import tempfile
from unittest.mock import patch

import independent_review
from independent_review import review_payload, source_sha256
from run_experiment import sha256 as producer_source_sha256


class IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.payload=json.loads((Path(__file__).parent/'RESULTS.json').read_text())

    def test_saved_original_inputs_and_outputs_replay(self):
        checked=review_payload(self.payload)
        self.assertEqual(checked['exact_equations_checked'],15)
        self.assertEqual(checked['unknown_no_claim_checked'],3)

    def test_changed_control_inputs_outputs_and_work_are_rejected(self):
        mutations=[]
        p=copy.deepcopy(self.payload);p['controls']['renamed_all_variables']['support']=[0];mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls']['positive_unit']['rhs']=0;mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls']['reordered_gadgets']['work']-=1;mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls']['added_binary_clause']['status']='EXACT_AFFINE';p['controls']['added_binary_clause']['support']=list(range(5));mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls']['duplicated_gadget']['original_input']['clauses'].append([1,2]);mutations.append(p)
        p=copy.deepcopy(self.payload);p['nonlinear_control']['projected_bits']=[1]*8;p['nonlinear_control']['status']='AFFINE';mutations.append(p)
        p=copy.deepcopy(self.payload);p['records'][0]['linear_algebra_baseline']['gadget_count']=0;mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls'].pop('added_empty_clause');mutations.append(p)
        p=copy.deepcopy(self.payload);p['records'][0]['original_input']['shared'][0]=False;mutations.append(p)
        p=copy.deepcopy(self.payload);p['controls']['added_binary_clause']['original_input']['clauses'][-1][0]=True;mutations.append(p)
        for index,payload in enumerate(mutations):
            with self.subTest(mutation=index),self.assertRaises(AssertionError):review_payload(payload)

    def test_lf_crlf_source_snapshots_replay_but_changed_source_is_rejected(self):
        originals={name:(Path(__file__).parent/name).read_bytes().decode('utf-8')
                   .replace('\r\n','\n').replace('\r','\n') for name in independent_review.SOURCE_NAMES}
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            for ending in ['\n','\r\n']:
                for name,text in originals.items():
                    (root/name).write_bytes(text.replace('\n',ending).encode('utf-8'))
                with patch.object(independent_review,'HERE',root):
                    self.assertTrue(review_payload(self.payload)['source_hashes_current'])
                for name in originals:
                    self.assertEqual(producer_source_sha256(root/name),self.payload['source_sha256'][name])
            changed=root/'engine.py'
            changed.write_bytes(changed.read_bytes()+b'\r\n# actual source edit\r\n')
            with patch.object(independent_review,'HERE',root),self.assertRaises(AssertionError):
                review_payload(self.payload)

    def test_text_hash_preserves_content_bom_and_utf8_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'source.py'
            path.write_bytes("name = 'caf\u00e9'\nvalue = 2\n".encode('utf-8'))
            expected=source_sha256(path)
            for content in ["name = 'caf\u00e9'\r\nvalue = 2\r\n", "name = 'caf\u00e9'\rvalue = 2\r"]:
                path.write_bytes(content.encode('utf-8'))
                self.assertEqual(source_sha256(path),expected)
                self.assertEqual(producer_source_sha256(path),expected)
            for content in ["name = 'caf\u00e9'\nvalue = 3\n", "name = 'caf\u00e9' \nvalue = 2\n", "\ufeffname = 'caf\u00e9'\nvalue = 2\n"]:
                path.write_bytes(content.encode('utf-8'))
                self.assertNotEqual(source_sha256(path),expected)
                self.assertEqual(source_sha256(path),producer_source_sha256(path))
            path.write_bytes(b'\xff')
            for hasher in [source_sha256,producer_source_sha256]:
                with self.assertRaises(UnicodeDecodeError):hasher(path)


if __name__=='__main__':unittest.main()
