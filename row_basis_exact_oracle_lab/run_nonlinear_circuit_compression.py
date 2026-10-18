"""Generate circuit-size records for the nonlinear weight boundary control."""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path

from explicit_code_family import generate_columns, parameters
from nonlinear_circuit_compression import circuit_gate_counts

HERE = Path(__file__).resolve().parent


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def run():
    source_names = ('explicit_code_family.py', 'nonlinear_circuit_compression.py')
    before = {name: digest(HERE / name) for name in source_names}
    degrees = [7, 8, 9]
    records = []
    for degree in degrees:
        spec = parameters(degree)
        _, forms = generate_columns(degree)
        counts = circuit_gate_counts(forms)
        assert len(forms) == spec['columns']
        records.append({'field_degree': degree, 'binary_rank': spec['binary_rank'],
                        'source_forms': len(forms), **counts})
    after = {name: digest(HERE / name) for name in source_names}
    assert before == after
    payload = {
        'status': 'NONLINEAR_CIRCUIT_COMPRESSION_CHECK_PASS',
        'timestamp_utc': datetime.now(timezone.utc).isoformat(),
        'degrees_checked': degrees,
        'records': records,
        'source_hashes_before': before,
        'source_hashes_after': after,
        'scope': 'Explicit XOR/AND circuit for the Hamming-weight objective; no solver or P-versus-NP claim.',
    }
    (HERE / 'NONLINEAR_CIRCUIT_COMPRESSION_RESULTS.json').write_text(
        json.dumps(payload, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'status': payload['status'], 'degrees': degrees,
                      'output_bits': [r['output_bits'] for r in records],
                      'total_gates': [r['total_gates'] for r in records]}))


if __name__ == '__main__':
    run()
