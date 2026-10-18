"""Reproduce the new integration, fast-probe and representation controls."""
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
LABS = ('affine_fast_recognition_lab','globally_compressed_affine_dag_lab',
        'affine_positive_cover_limits_lab','affine_gram_conditioning_lab',
        'affine_character_factor_lab','connected_affine_cover_lab',
        'mixed_information_frontier_lab','linear_frontier_order_lab',
        'graph_order_hardness_lab','variable_boundary_sat_lab',
        'primal_order_sat_lab','row_basis_exact_oracle_lab','circuit_boundary_lab',
        'circuit_order_hardness_lab','local_marginal_code_lab')


def digest(path): return sha256(path.read_bytes()).hexdigest()


def source_hashes():
    paths=[]
    for lab in LABS:
        paths.extend(p for p in (HERE/lab).glob('*.py') if p.name != '__init__.py')
    paths.extend([HERE/'AFFINE_RECOGNITION_INTEGRATION_REPORT.md',
                  HERE/'AFFINE_CANCELLATION_LITERATURE_SCOPE.md',
                  HERE/'run_followup_phase_checks.py',
                  HERE/'VERIFY_FOLLOWUP_ARTIFACTS.py',
                  HERE/'rank_native_solver.py', HERE/'native_coset_solver.py',
                  HERE/'matching_certificate.py',
                  HERE/'row_basis_exact_oracle_lab'/'rank5_exact.cpp'])
    return {p.relative_to(HERE).as_posix():digest(p) for p in sorted(paths)}


def run(cmd, cwd):
    started=time.perf_counter()
    result=subprocess.run([sys.executable,*cmd],cwd=cwd,capture_output=True,text=True,timeout=900)
    output=result.stdout+result.stderr
    found=re.findall(r'Ran (\d+) tests? in',output)
    return dict(command=' '.join(cmd),cwd=Path(cwd).name,returncode=result.returncode,
                passed=result.returncode==0,tests=int(found[-1]) if found else None,
                seconds=time.perf_counter()-started,output=output)


def main():
    before=source_hashes(); started=datetime.now(timezone.utc).isoformat(); rows=[]
    for lab in LABS[:3]: rows.append(run(['-m','unittest','discover','-v'],HERE/lab))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'affine_character_factor_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'connected_affine_cover_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'mixed_information_frontier_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'linear_frontier_order_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'graph_order_hardness_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'variable_boundary_sat_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'primal_order_sat_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'circuit_boundary_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'circuit_order_hardness_lab'))
    rows.append(run(['-m','unittest','discover','-v'],HERE/'local_marginal_code_lab'))
    rows.append(run(['check.py'],HERE/'affine_gram_conditioning_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'affine_fast_recognition_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'affine_positive_cover_limits_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'affine_gram_conditioning_lab'))
    rows.append(run(['VERIFY_COMPARISON.py'],HERE/'globally_compressed_affine_dag_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'affine_character_factor_lab'))
    rows.append(run(['verify_elimination_controls.py'],HERE/'affine_character_factor_lab'))
    rows.append(run(['verify_order_controls.py'],HERE/'affine_character_factor_lab'))
    rows.append(run(['verify_auto_route_controls.py'],HERE/'affine_character_factor_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'connected_affine_cover_lab'))
    rows.append(run(['verify_weighted_crosscheck.py'],HERE/'connected_affine_cover_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'mixed_information_frontier_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'linear_frontier_order_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'graph_order_hardness_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'variable_boundary_sat_lab'))
    rows.append(run(['EXHAUSTIVE_SMALL_CHECK.py'],HERE/'variable_boundary_sat_lab'))
    rows.append(run(['REDUNDANCY_ADVERSARY.py'],HERE/'variable_boundary_sat_lab'))
    rows.append(run(['INDEPENDENT_REDUNDANCY_REVIEW.py'],HERE/'variable_boundary_sat_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'primal_order_sat_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['RANK5_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['EXCEPTION_RANK_BOUND_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['PROJECTIVE_FAMILY_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['EXPLICIT_CODE_FAMILY_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['LINEAR_WEIGHT_SIGNATURE_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['AFFINE_WEIGHT_SIGNATURE_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['NONLINEAR_WEIGHT_COMPRESSION_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.py'],HERE/'row_basis_exact_oracle_lab'))
    rows.append(run(['run_experiments.py'],HERE/'circuit_boundary_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'circuit_boundary_lab'))
    rows.append(run(['run_experiments.py'],HERE/'circuit_order_hardness_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'circuit_order_hardness_lab'))
    rows.append(run(['run_experiments.py'],HERE/'local_marginal_code_lab'))
    rows.append(run(['INDEPENDENT_REVIEW.py'],HERE/'local_marginal_code_lab'))
    after=source_hashes(); assert before==after
    assert all(row['passed'] for row in rows)
    tests=sum(row['tests'] or 0 for row in rows)
    result=dict(status='FOLLOWUP_CHECKS_PASS',started_utc=started,
                finished_utc=datetime.now(timezone.utc).isoformat(),source_hashes_before=before,
                source_hashes_after=after,source_unchanged_during_run=True,
                total_unit_tests=tests,rows=rows,
                scope='New integration and representation controls only; no P-versus-NP resolution claim.')
    (HERE/'FOLLOWUP_TEST_SUMMARY.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'status':result['status'],'total_unit_tests':tests,'checks':len(rows)}))


if __name__=='__main__': main()
