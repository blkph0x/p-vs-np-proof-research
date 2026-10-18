"""Bind the final follow-up phase files without repeating expensive searches."""
from hashlib import sha256
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def digest(path): return sha256(path.read_bytes()).hexdigest()


def bind(path, expected=None):
    assert path.is_file(), path
    actual=digest(path)
    if expected is not None: assert actual==expected, (path,actual,expected)
    return actual


def main():
    summary=json.loads((HERE/'FOLLOWUP_TEST_SUMMARY.json').read_text())
    assert summary['all_tests_passed'] and summary['source_unchanged_during_tests']
    assert summary['test_count']==41 and summary['suite_count']==5
    for name,expected in summary['implementation_sha256'].items(): bind(HERE/name,expected)
    fast=json.loads((HERE/'affine_fast_recognition_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert fast['status']=='VERIFIED_FAST_WRAPPER_REVIEW'
    assert fast['saved_requests']==494 and fast['direct_truth_table_cases']==464
    gram=json.loads((HERE/'affine_gram_conditioning_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert gram['verdict']=='CLEAN' and gram['summary']['original_cases']==28 and gram['summary']['original_truth_words']==8190
    positive=json.loads((HERE/'affine_positive_cover_limits_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert positive['status']=='VERIFIED_INDEPENDENT_CONTROLS' and positive['original_truth_words']==4681
    comparison=json.loads((HERE/'globally_compressed_affine_dag_lab'/'COMPARISON_AUDIT.json').read_text())
    assert comparison['status']=='VERIFIED_COMPARISON_BINDINGS' and comparison['cases']==80
    assert comparison['summary']=={'stress22':{'VERIFIED_EXACT':11,'UNKNOWN':11},
                                   'original58':{'VERIFIED_EXACT':54,'UNKNOWN':4}}
    assert comparison['recognition_exact']==0 and comparison['recognition_rejections']==3453
    character=json.loads((HERE/'affine_character_factor_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert character['status']=='VERIFIED_INDEPENDENT_CHARACTER_REVIEW'
    assert character['records']==23 and character['exact']==21 and character['unknown']==1
    assert character['invalid_controls']==1 and character['exact_replayed']==21
    elimination=json.loads((HERE/'affine_character_factor_lab'/'ELIMINATION_REVIEW.json').read_text())
    assert elimination['status']=='VERIFIED_INDEPENDENT_ELIMINATION_REVIEW'
    assert elimination['rows']==9 and elimination['exact']==8 and elimination['unknown']==1
    assert elimination['exact_replayed']==8 and elimination['interleaved_chain_128_peak_terms']==3
    order=json.loads((HERE/'affine_character_factor_lab'/'ORDER_DISCOVERY_REVIEW.json').read_text())
    assert order['status']=='VERIFIED_INDEPENDENT_ORDER_REVIEW'
    assert order['rows']==7 and order['chain_exact_replayed']==3
    assert order['complete_status']=='NO' and order['cycle_status']=='NO'
    assert order['budget_status']=='UNKNOWN'
    auto=json.loads((HERE/'affine_character_factor_lab'/'AUTO_ROUTE_REVIEW.json').read_text())
    assert auto['status']=='VERIFIED_INDEPENDENT_AUTO_ROUTE_REVIEW'
    assert auto['rows']==6 and auto['exact']==3 and auto['no']==2 and auto['unknown']==1
    assert auto['chain_128_peak_terms']==3
    cover=json.loads((HERE/'connected_affine_cover_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert cover['status']=='VERIFIED_INDEPENDENT_CONNECTED_AFFINE_REVIEW'
    assert cover['small_cases']==7 and cover['all_size_cases']==8
    assert cover['n256_lower_bound']==1090151200392118
    weighted=json.loads((HERE/'connected_affine_cover_lab'/'WEIGHTED_REVIEW.json').read_text())
    assert weighted['status']=='VERIFIED_INDEPENDENT_WEIGHTED_CROSSCHECK'
    assert weighted['row_count']==5 and weighted['exact_count']==5
    assert weighted['max_peak_terms']==4
    frontier=json.loads((HERE/'mixed_information_frontier_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert frontier['status']=='VERIFIED_INDEPENDENT_MIXED_FRONTIER_REVIEW'
    assert frontier['case_count']==6
    assert frontier['full_product_case_classes']==64
    assert frontier['duplicate_parity_classes']==2
    assert frontier['same_scope_cardinality_parity_classes']==7
    assert frontier['partial_scope_cardinality_parity_classes']==10
    linear=json.loads((HERE/'linear_frontier_order_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert linear['status']=='VERIFIED_INDEPENDENT_LINEAR_FRONTIER_REVIEW'
    assert linear['case_count']==4
    assert linear['crossing_bad_width']==6 and linear['crossing_optimal_width']==1
    graph=json.loads((HERE/'graph_order_hardness_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert graph['status']=='VERIFIED_INDEPENDENT_VERTEX_SEPARATION_REVIEW'
    assert graph['case_count']==5
    assert graph['star_bad_width']==7 and graph['star_optimal_width']==1
    assert graph['bipartite_greedy_width']==4 and graph['bipartite_optimal_width']==2
    variable=json.loads((HERE/'variable_boundary_sat_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert variable['status']=='VERIFIED_INDEPENDENT_VARIABLE_BOUNDARY_REVIEW'
    assert variable['case_count']==5
    assert variable['chain_64_width']==1
    assert variable['star_bad_width']==11 and variable['star_good_width']==1
    exhaustive=json.loads((HERE/'variable_boundary_sat_lab'/'EXHAUSTIVE_SMALL_CHECK.json').read_text())
    assert exhaustive['status']=='EXHAUSTIVE_SMALL_BOUNDARY_CROSSCHECK_PASS'
    assert exhaustive['variables']==3 and exhaustive['max_clauses']==3
    assert exhaustive['cnfs']==2952 and exhaustive['orders']==6 and exhaustive['certificates']==17712
    redundancy=json.loads((HERE/'variable_boundary_sat_lab'/'REDUNDANCY_ADVERSARY.json').read_text())
    assert redundancy['status']=='REDUNDANCY_ADVERSARY_PASS' and len(redundancy['rows'])==6
    redundancy_review=json.loads((HERE/'variable_boundary_sat_lab'/'INDEPENDENT_REDUNDANCY_REVIEW.json').read_text())
    assert redundancy_review['status']=='VERIFIED_INDEPENDENT_REDUNDANCY_REVIEW'
    assert redundancy_review['case_count']==6
    assert redundancy_review['largest_raw_states']==766
    assert redundancy_review['largest_normalized_states']==25
    primal=json.loads((HERE/'primal_order_sat_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert primal['status']=='VERIFIED_INDEPENDENT_PRIMAL_ORDER_REVIEW'
    assert primal['case_count']==6 and primal['exact_count']==5 and primal['unknown_count']==1
    assert primal['chain_width']==1 and primal['complete_width']==5
    oracle=json.loads((HERE/'row_basis_exact_oracle_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert oracle['status']=='VERIFIED_INDEPENDENT_ROW_BASIS_ORACLE_REVIEW'
    assert oracle['case_count']==11 and oracle['exact_count']==10 and oracle['unknown_count']==1
    assert oracle['gl3_trap_exact']==[1,1,31]
    assert oracle['gl3_trap_heuristic']==[2,2,33]
    assert oracle['rank_tradeoff_q_objective']==[2,2,28]
    assert oracle['rank_tradeoff_p_objective']==[1,4,4,31]
    assert oracle['rank_tradeoff_heuristic_stats']==[2,2,2,28]
    assert oracle['rank_tradeoff_native_q_state_count']==4
    assert oracle['rank_tradeoff_native_p_state_count']==2
    assert oracle['rank_tradeoff_native_distance']==2
    assert oracle['rank_tradeoff_rank_aware_objective']==[1,4,4,31]
    assert oracle['rank_tradeoff_rank_aware_state_count']==2
    rank5=json.loads((HERE/'row_basis_exact_oracle_lab'/'RANK5_REVIEW.json').read_text())
    assert rank5['status']=='VERIFIED_INDEPENDENT_RANK5_REVIEW'
    assert rank5['group_size']==9999360 and rank5['case_count']==4
    assert rank5['tradeoff_count_first_state_count']==4
    assert rank5['tradeoff_rank_first_state_count']==2
    assert rank5['tradeoff_distance']==2
    bound=json.loads((HERE/'row_basis_exact_oracle_lab'/'EXCEPTION_RANK_BOUND_REVIEW.json').read_text())
    assert bound['status']=='VERIFIED_INDEPENDENT_EXCEPTION_RANK_BOUND'
    assert bound['ranks_checked']==[6,7,8,16,32]
    assert bound['rank32_columns']==16416 and bound['rank32_states']==4294967296
    projective=json.loads((HERE/'row_basis_exact_oracle_lab'/'PROJECTIVE_FAMILY_REVIEW.json').read_text())
    assert projective['status']=='VERIFIED_INDEPENDENT_PROJECTIVE_FAMILY'
    assert projective['ranks_checked']==[4,5,6,7,8,12]
    assert projective['rank12_columns']==4095 and projective['rank12_states']==4096
    explicit=json.loads((HERE/'row_basis_exact_oracle_lab'/'EXPLICIT_CODE_FAMILY_REVIEW.json').read_text())
    assert explicit['status']=='VERIFIED_INDEPENDENT_EXPLICIT_CODE_FAMILY'
    assert explicit['degrees_checked']==[7,8,9]
    assert explicit['rank7_states']==16384
    assert explicit['rank8_states']==4294967296
    assert explicit['rank9_states']==18014398509481984
    assert explicit['k7_exhaustive_minimum_distance']==8128
    pullback=json.loads((HERE/'row_basis_exact_oracle_lab'/'EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.json').read_text())
    assert pullback['status']=='VERIFIED_INDEPENDENT_EXPLICIT_OBJECTIVE_PULLBACK'
    assert pullback['degrees_checked']==[7,8,9]
    assert [row['defect'] for row in pullback['rows']]==[8192,32768,131072]
    signature=json.loads((HERE/'row_basis_exact_oracle_lab'/'LINEAR_WEIGHT_SIGNATURE_REVIEW.json').read_text())
    assert signature['status']=='VERIFIED_INDEPENDENT_LINEAR_WEIGHT_SIGNATURE'
    assert signature['degrees_checked']==[7,8,9]
    assert [row['forced_positive_rows'] for row in signature['rows']]==[16256,65280,261632]
    assert signature['small_cube_assignments_checked']==8
    affine_signature=json.loads((HERE/'row_basis_exact_oracle_lab'/'AFFINE_WEIGHT_SIGNATURE_REVIEW.json').read_text())
    assert affine_signature['status']=='VERIFIED_INDEPENDENT_AFFINE_WEIGHT_SIGNATURE'
    assert affine_signature['degrees_checked']==[7,8,9]
    assert [row['forced_nonzero_rows'] for row in affine_signature['rows']]==[16256,65280,261632]
    assert affine_signature['small_cube_assignments_checked']==8
    assert affine_signature['signed_weights_accepted'] is True
    nonlinear=json.loads((HERE/'row_basis_exact_oracle_lab'/'NONLINEAR_WEIGHT_COMPRESSION_REVIEW.json').read_text())
    assert nonlinear['status']=='VERIFIED_INDEPENDENT_NONLINEAR_WEIGHT_COMPRESSION'
    assert nonlinear['degrees_checked']==[7,8,9]
    assert [row['nonlinear_digit_rows'] for row in nonlinear['rows']]==[14,16,18]
    assert nonlinear['small_cube_assignments_checked']==32
    assert nonlinear['threshold_control'] is True
    nonlinear_circuit=json.loads((HERE/'row_basis_exact_oracle_lab'/'NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.json').read_text())
    assert nonlinear_circuit['status']=='VERIFIED_INDEPENDENT_NONLINEAR_CIRCUIT_COMPRESSION'
    assert nonlinear_circuit['degrees_checked']==[7,8,9]
    assert [row['output_bits'] for row in nonlinear_circuit['rows']]==[14,16,18]
    assert [row['total_gates'] for row in nonlinear_circuit['rows']]==[553152,3069184,16223488]
    assert nonlinear_circuit['small_cube_assignments_checked']==32
    circuit=json.loads((HERE/'circuit_boundary_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert circuit['status']=='VERIFIED_INDEPENDENT_CIRCUIT_BOUNDARY'
    assert circuit['assignments_checked']==32
    assert circuit['gate_clauses_checked']==174
    assert circuit['max_width']==11
    assert circuit['all_gate_truth_tables_checked'] is True
    assert circuit['all_outputs_match_direct_weight'] is True
    assert circuit['all_wrong_targets_rejected_by_producer'] is True
    order_control=json.loads((HERE/'circuit_boundary_lab'/'RESULTS.json').read_text())['order_control']
    assert order_control['variables']==18 and order_control['clauses']==48
    assert order_control['topological_width']==6 and order_control['optimal_width']==4
    assert order_control['subset_state_count']==262144
    distance=json.loads((HERE/'circuit_boundary_lab'/'RESULTS.json').read_text())['distance_control']
    assert distance['minimum_nonzero_weight']==4
    assert [row['sat'] for row in distance['queries']]==[False,False,False,False,True]
    assert [row['states'] for row in distance['queries']]==[304,306,306,308,307]
    assert all(row['max_width']==11 for row in distance['queries'])
    compact=distance['compact_circuits']
    assert [item['variables'] for item in compact]==[62,64,64,66,64]
    assert [len(item['clauses']) for item in compact]==[191,197,197,203,197]
    assert all('comparator' in item for item in compact)
    circuit_order=json.loads((HERE/'circuit_order_hardness_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert circuit_order['status']=='VERIFIED_INDEPENDENT_CIRCUIT_ORDER_BOUND'
    assert circuit_order['case_count']==5
    assert circuit_order['all_lower_bounds_hold'] is True
    assert circuit_order['all_additive_upper_bounds_hold'] is True
    assert circuit_order['all_controls_trivially_satisfiable'] is True
    assert max(row['source_width'] for row in circuit_order['rows'])==3
    assert max(row['full_width'] for row in circuit_order['rows'])==4
    circuit_order_results=json.loads((HERE/'circuit_order_hardness_lab'/'RESULTS.json').read_text())
    assert circuit_order_results['all_lower_bounds_hold'] is True
    assert circuit_order_results['all_additive_upper_bounds_hold'] is True
    local=json.loads((HERE/'local_marginal_code_lab'/'INDEPENDENT_REVIEW.json').read_text())
    assert local['status']=='VERIFIED_INDEPENDENT_LOCAL_MARGINAL_BOUND'
    assert local['case_count']==3 and local['golay_level']==6 and local['golay_gap']==8
    assert local['rows'][0]['theorem_level_valid'] is True
    assert local['rows'][1]['theorem_level_valid'] is False
    assert local['rows'][2]['dual_distance']==8
    assert local['rows'][2]['pinned_integer_optimum']==8
    local_results=json.loads((HERE/'local_marginal_code_lab'/'RESULTS.json').read_text())
    assert local_results['all_valid'] is True
    assert local_results['golay_level_bound_verified'] is True
    assert local_results['golay_support_replay_deferred'] is True
    assert [row['n'] for row in local_results['random_code_bounds']]==[32,64,128,256,512,1024]
    assert [row['local_level_lower_bound'] for row in local_results['random_code_bounds']]==[0,2,6,14,30,62]
    assert all(row['strictly_positive_good_probability'] for row in local_results['random_code_bounds'])
    # Bind all final evidence and prose files at their present bytes.
    files=[
        'AFFINE_RECOGNITION_INTEGRATION_REPORT.md','AFFINE_CANCELLATION_LITERATURE_SCOPE.md',
        'FOLLOWUP_TEST_SUMMARY.json','run_followup_phase_checks.py','VERIFY_FOLLOWUP_ARTIFACTS.py',
        'globally_compressed_affine_dag_lab/COMPARISON_RESULTS.json',
        'globally_compressed_affine_dag_lab/COMPARISON_AUDIT.json',
        'globally_compressed_affine_dag_lab/run_comparison.py',
        'globally_compressed_affine_dag_lab/VERIFY_COMPARISON.py',
        'globally_compressed_affine_dag_lab/POLICY.md',
        'affine_fast_recognition_lab/INDEPENDENT_REVIEW.json',
        'affine_fast_recognition_lab/INDEPENDENT_REVIEW.md',
        'affine_positive_cover_limits_lab/INDEPENDENT_REVIEW.json',
        'affine_positive_cover_limits_lab/INDEPENDENT_REVIEW.md',
        'affine_gram_conditioning_lab/INDEPENDENT_REVIEW.json',
        'affine_gram_conditioning_lab/INDEPENDENT_REVIEW.md',
        'affine_character_factor_lab/RESULTS.json',
        'affine_character_factor_lab/THEOREM.md',
        'affine_character_factor_lab/INDEPENDENT_REVIEW.json',
        'affine_character_factor_lab/INDEPENDENT_REVIEW.md',
        'affine_character_factor_lab/run_experiments.py',
        'affine_character_factor_lab/engine.py',
        'affine_character_factor_lab/test_engine.py',
        'affine_character_factor_lab/INDEPENDENT_REVIEW.py',
        'affine_character_factor_lab/ELIMINATION_RESULTS.json',
        'affine_character_factor_lab/ELIMINATION_REPORT.md',
        'affine_character_factor_lab/ELIMINATION_REVIEW.json',
        'affine_character_factor_lab/ELIMINATION_REVIEW.md',
        'affine_character_factor_lab/elimination_controls.py',
        'affine_character_factor_lab/verify_elimination_controls.py',
        'affine_character_factor_lab/ORDER_DISCOVERY_RESULTS.json',
        'affine_character_factor_lab/ORDER_DISCOVERY_THEOREM.md',
        'affine_character_factor_lab/ORDER_DISCOVERY_REVIEW.json',
        'affine_character_factor_lab/ORDER_DISCOVERY_REVIEW.md',
        'affine_character_factor_lab/run_order_controls.py',
        'affine_character_factor_lab/verify_order_controls.py',
        'affine_character_factor_lab/order_discovery.py',
        'affine_character_factor_lab/test_order_discovery.py',
        'affine_character_factor_lab/AUTO_ROUTE_RESULTS.json',
        'affine_character_factor_lab/AUTO_ROUTE_THEOREM.md',
        'affine_character_factor_lab/AUTO_ROUTE_REVIEW.json',
        'affine_character_factor_lab/AUTO_ROUTE_REVIEW.md',
        'affine_character_factor_lab/auto_route.py',
        'affine_character_factor_lab/test_auto_route.py',
        'affine_character_factor_lab/run_auto_route_controls.py',
        'affine_character_factor_lab/verify_auto_route_controls.py',
        'connected_affine_cover_lab/RESULTS.json',
        'connected_affine_cover_lab/THEOREM.md',
        'connected_affine_cover_lab/INDEPENDENT_REVIEW.json',
        'connected_affine_cover_lab/INDEPENDENT_REVIEW.md',
        'connected_affine_cover_lab/cover.py',
        'connected_affine_cover_lab/test_cover.py',
        'connected_affine_cover_lab/run_experiments.py',
        'connected_affine_cover_lab/INDEPENDENT_REVIEW.py',
        'connected_affine_cover_lab/WEIGHTED_RESULTS.json',
        'connected_affine_cover_lab/WEIGHTED_REVIEW.json',
        'connected_affine_cover_lab/WEIGHTED_REVIEW.md',
        'connected_affine_cover_lab/weighted_crosscheck.py',
        'connected_affine_cover_lab/verify_weighted_crosscheck.py',
        'mixed_information_frontier_lab/RESULTS.json',
        'mixed_information_frontier_lab/THEOREM.md',
        'mixed_information_frontier_lab/INDEPENDENT_REVIEW.json',
        'mixed_information_frontier_lab/INDEPENDENT_REVIEW.md',
        'mixed_information_frontier_lab/README.md',
        'mixed_information_frontier_lab/EQUIVALENCE_HARDNESS.md',
        'mixed_information_frontier_lab/test_equivalence_reduction.py',
        'mixed_information_frontier_lab/mixed_frontier.py',
        'mixed_information_frontier_lab/test_mixed_frontier.py',
        'mixed_information_frontier_lab/run_experiments.py',
        'mixed_information_frontier_lab/INDEPENDENT_REVIEW.py',
        'linear_frontier_order_lab/RESULTS.json',
        'linear_frontier_order_lab/THEOREM.md',
        'linear_frontier_order_lab/README.md',
        'linear_frontier_order_lab/INDEPENDENT_REVIEW.json',
        'linear_frontier_order_lab/INDEPENDENT_REVIEW.md',
        'linear_frontier_order_lab/frontier.py',
        'linear_frontier_order_lab/test_frontier.py',
        'linear_frontier_order_lab/run_experiments.py',
        'linear_frontier_order_lab/INDEPENDENT_REVIEW.py',
        'graph_order_hardness_lab/RESULTS.json',
        'graph_order_hardness_lab/THEOREM.md',
        'graph_order_hardness_lab/README.md',
        'graph_order_hardness_lab/INDEPENDENT_REVIEW.json',
        'graph_order_hardness_lab/INDEPENDENT_REVIEW.md',
        'graph_order_hardness_lab/vertex_separation.py',
        'graph_order_hardness_lab/test_vertex_separation.py',
        'graph_order_hardness_lab/run_experiments.py',
        'graph_order_hardness_lab/INDEPENDENT_REVIEW.py',
        'variable_boundary_sat_lab/RESULTS.json',
        'variable_boundary_sat_lab/THEOREM.md',
        'variable_boundary_sat_lab/README.md',
        'variable_boundary_sat_lab/INDEPENDENT_REVIEW.json',
        'variable_boundary_sat_lab/INDEPENDENT_REVIEW.md',
        'variable_boundary_sat_lab/boundary_dp.py',
        'variable_boundary_sat_lab/test_boundary_dp.py',
        'variable_boundary_sat_lab/run_experiments.py',
        'variable_boundary_sat_lab/INDEPENDENT_REVIEW.py',
        'variable_boundary_sat_lab/EXHAUSTIVE_SMALL_CHECK.json',
        'variable_boundary_sat_lab/EXHAUSTIVE_SMALL_CHECK.py',
        'variable_boundary_sat_lab/REDUNDANCY_ADVERSARY.json',
        'variable_boundary_sat_lab/REDUNDANCY_ADVERSARY.py',
        'variable_boundary_sat_lab/INDEPENDENT_REDUNDANCY_REVIEW.json',
        'variable_boundary_sat_lab/INDEPENDENT_REDUNDANCY_REVIEW.md',
        'variable_boundary_sat_lab/INDEPENDENT_REDUNDANCY_REVIEW.py',
        'variable_boundary_sat_lab/REDUNDANCY_THEOREM.md',
        'primal_order_sat_lab/RESULTS.json',
        'primal_order_sat_lab/THEOREM.md',
        'primal_order_sat_lab/README.md',
        'primal_order_sat_lab/INDEPENDENT_REVIEW.json',
        'primal_order_sat_lab/INDEPENDENT_REVIEW.md',
        'primal_order_sat_lab/primal_order.py',
        'primal_order_sat_lab/test_primal_order.py',
        'primal_order_sat_lab/run_experiments.py',
        'primal_order_sat_lab/INDEPENDENT_REVIEW.py',
        'row_basis_exact_oracle_lab/RESULTS.json',
        'row_basis_exact_oracle_lab/THEOREM.md',
        'row_basis_exact_oracle_lab/README.md',
        'row_basis_exact_oracle_lab/INDEPENDENT_REVIEW.json',
        'row_basis_exact_oracle_lab/INDEPENDENT_REVIEW.md',
        'row_basis_exact_oracle_lab/exact_oracle.py',
        'row_basis_exact_oracle_lab/test_exact_oracle.py',
        'row_basis_exact_oracle_lab/rank_aware_discovery.py',
        'row_basis_exact_oracle_lab/test_rank_aware.py',
        'row_basis_exact_oracle_lab/run_experiments.py',
        'row_basis_exact_oracle_lab/INDEPENDENT_REVIEW.py',
        'row_basis_exact_oracle_lab/RANK5_RESULTS.json',
        'row_basis_exact_oracle_lab/RANK5_REVIEW.json',
        'row_basis_exact_oracle_lab/RANK5_REVIEW.md',
        'row_basis_exact_oracle_lab/RANK5_THEOREM.md',
        'row_basis_exact_oracle_lab/rank5_exact.cpp',
        'row_basis_exact_oracle_lab/rank5_driver.py',
        'row_basis_exact_oracle_lab/RANK5_REVIEW.py',
        'row_basis_exact_oracle_lab/test_rank5_artifact.py',
        'row_basis_exact_oracle_lab/EXCEPTION_RANK_BOUND_RESULTS.json',
        'row_basis_exact_oracle_lab/EXCEPTION_RANK_BOUND_REVIEW.json',
        'row_basis_exact_oracle_lab/EXCEPTION_RANK_BOUND_REVIEW.md',
        'row_basis_exact_oracle_lab/EXCEPTION_RANK_BOUND.md',
        'row_basis_exact_oracle_lab/exception_rank_bound.py',
        'row_basis_exact_oracle_lab/run_exception_rank_bound.py',
        'row_basis_exact_oracle_lab/EXCEPTION_RANK_BOUND_REVIEW.py',
        'row_basis_exact_oracle_lab/test_exception_rank_bound.py',
        'row_basis_exact_oracle_lab/PROJECTIVE_FAMILY_RESULTS.json',
        'row_basis_exact_oracle_lab/PROJECTIVE_FAMILY_REVIEW.json',
        'row_basis_exact_oracle_lab/PROJECTIVE_FAMILY_REVIEW.md',
        'row_basis_exact_oracle_lab/PROJECTIVE_FAMILY.md',
        'row_basis_exact_oracle_lab/projective_family.py',
        'row_basis_exact_oracle_lab/run_projective_family.py',
        'row_basis_exact_oracle_lab/PROJECTIVE_FAMILY_REVIEW.py',
        'row_basis_exact_oracle_lab/test_projective_family.py',
        'row_basis_exact_oracle_lab/EXPLICIT_CODE_FAMILY_RESULTS.json',
        'row_basis_exact_oracle_lab/EXPLICIT_CODE_FAMILY_REVIEW.json',
        'row_basis_exact_oracle_lab/EXPLICIT_CODE_FAMILY_REVIEW.md',
        'row_basis_exact_oracle_lab/EXPLICIT_CODE_FAMILY.md',
        'row_basis_exact_oracle_lab/explicit_code_family.py',
        'row_basis_exact_oracle_lab/run_explicit_code_family.py',
        'row_basis_exact_oracle_lab/EXPLICIT_CODE_FAMILY_REVIEW.py',
        'row_basis_exact_oracle_lab/test_explicit_code_family.py',
        'row_basis_exact_oracle_lab/EXPLICIT_OBJECTIVE_PULLBACK_RESULTS.json',
        'row_basis_exact_oracle_lab/EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.json',
        'row_basis_exact_oracle_lab/EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.md',
        'row_basis_exact_oracle_lab/explicit_objective_pullback.py',
        'row_basis_exact_oracle_lab/run_explicit_objective_pullback.py',
        'row_basis_exact_oracle_lab/EXPLICIT_OBJECTIVE_PULLBACK_REVIEW.py',
        'row_basis_exact_oracle_lab/test_explicit_objective_pullback.py',
        'row_basis_exact_oracle_lab/LINEAR_WEIGHT_SIGNATURE_RESULTS.json',
        'row_basis_exact_oracle_lab/LINEAR_WEIGHT_SIGNATURE_REVIEW.json',
        'row_basis_exact_oracle_lab/LINEAR_WEIGHT_SIGNATURE_REVIEW.md',
        'row_basis_exact_oracle_lab/LINEAR_WEIGHT_SIGNATURE.md',
        'row_basis_exact_oracle_lab/linear_weight_signature.py',
        'row_basis_exact_oracle_lab/run_linear_weight_signature.py',
        'row_basis_exact_oracle_lab/LINEAR_WEIGHT_SIGNATURE_REVIEW.py',
        'row_basis_exact_oracle_lab/test_linear_weight_signature.py',
        'row_basis_exact_oracle_lab/AFFINE_WEIGHT_SIGNATURE_RESULTS.json',
        'row_basis_exact_oracle_lab/AFFINE_WEIGHT_SIGNATURE_REVIEW.json',
        'row_basis_exact_oracle_lab/AFFINE_WEIGHT_SIGNATURE_REVIEW.md',
        'row_basis_exact_oracle_lab/AFFINE_WEIGHT_SIGNATURE.md',
        'row_basis_exact_oracle_lab/affine_weight_signature.py',
        'row_basis_exact_oracle_lab/run_affine_weight_signature.py',
        'row_basis_exact_oracle_lab/AFFINE_WEIGHT_SIGNATURE_REVIEW.py',
        'row_basis_exact_oracle_lab/test_affine_weight_signature.py',
        'row_basis_exact_oracle_lab/NONLINEAR_WEIGHT_COMPRESSION_RESULTS.json',
        'row_basis_exact_oracle_lab/NONLINEAR_WEIGHT_COMPRESSION_REVIEW.json',
        'row_basis_exact_oracle_lab/NONLINEAR_WEIGHT_COMPRESSION_REVIEW.md',
        'row_basis_exact_oracle_lab/NONLINEAR_WEIGHT_COMPRESSION.md',
        'row_basis_exact_oracle_lab/nonlinear_weight_compression.py',
        'row_basis_exact_oracle_lab/run_nonlinear_weight_compression.py',
        'row_basis_exact_oracle_lab/NONLINEAR_WEIGHT_COMPRESSION_REVIEW.py',
        'row_basis_exact_oracle_lab/test_nonlinear_weight_compression.py',
        'row_basis_exact_oracle_lab/NONLINEAR_CIRCUIT_COMPRESSION_RESULTS.json',
        'row_basis_exact_oracle_lab/NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.json',
        'row_basis_exact_oracle_lab/NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.md',
        'row_basis_exact_oracle_lab/NONLINEAR_CIRCUIT_COMPRESSION.md',
        'row_basis_exact_oracle_lab/nonlinear_circuit_compression.py',
        'row_basis_exact_oracle_lab/run_nonlinear_circuit_compression.py',
        'row_basis_exact_oracle_lab/NONLINEAR_CIRCUIT_COMPRESSION_REVIEW.py',
        'row_basis_exact_oracle_lab/test_nonlinear_circuit_compression.py',
        'circuit_boundary_lab/RESULTS.json',
        'circuit_boundary_lab/INDEPENDENT_REVIEW.json',
        'circuit_boundary_lab/INDEPENDENT_REVIEW.md',
        'circuit_boundary_lab/circuit_cnf.py',
        'circuit_boundary_lab/run_experiments.py',
        'circuit_boundary_lab/test_circuit_cnf.py',
        'circuit_boundary_lab/THEOREM.md',
        'circuit_boundary_lab/README.md',
        'circuit_order_hardness_lab/RESULTS.json',
        'circuit_order_hardness_lab/INDEPENDENT_REVIEW.json',
        'circuit_order_hardness_lab/INDEPENDENT_REVIEW.md',
        'circuit_order_hardness_lab/circuit_order.py',
        'circuit_order_hardness_lab/run_experiments.py',
        'circuit_order_hardness_lab/test_circuit_order.py',
        'circuit_order_hardness_lab/THEOREM.md',
        'circuit_order_hardness_lab/README.md',
        'local_marginal_code_lab/RESULTS.json',
        'local_marginal_code_lab/INDEPENDENT_REVIEW.json',
        'local_marginal_code_lab/INDEPENDENT_REVIEW.md',
        'local_marginal_code_lab/local_marginal.py',
        'local_marginal_code_lab/random_code_bound.py',
        'local_marginal_code_lab/run_experiments.py',
        'local_marginal_code_lab/test_local_marginal.py',
        'local_marginal_code_lab/THEOREM.md',
        'local_marginal_code_lab/README.md',
        'rank_native_solver.py',
        'native_coset_solver.py',
        'matching_certificate.py',
    ]
    hashes={name:bind(HERE/name) for name in files}
    output=dict(status='VERIFIED_FOLLOWUP_ARTIFACT_BINDINGS',files=len(hashes),
                unit_tests=summary['test_count'],fast_saved_requests=494,fast_direct_cases=464,
                positive_truth_words=4681,gram_truth_words=8190,comparison_cases=80,
                character_records=23,character_exact=21,character_unknown=1,
                elimination_rows=9,elimination_exact=8,elimination_unknown=1,
                order_rows=7,order_chain_exact=3,order_budget_unknown=1,
                auto_route_rows=6,auto_route_exact=3,auto_route_no=2,auto_route_unknown=1,
                connected_cover_small_cases=7,connected_cover_all_size_cases=8,
                connected_cover_n256_lower_bound=1090151200392118,
                connected_weighted_rows=5,connected_weighted_exact=5,
                connected_weighted_max_peak_terms=4,
                mixed_frontier_cases=6,mixed_frontier_full_product_classes=64,
                mixed_frontier_duplicate_parity_classes=2,
                mixed_frontier_same_scope_cardinality_classes=7,
                mixed_frontier_partial_scope_cardinality_classes=10,
                mixed_frontier_equivalence_reduction_tests=3,
                linear_frontier_cases=4,linear_frontier_crossing_bad_width=6,
                linear_frontier_crossing_optimal_width=1,
                graph_order_cases=5,graph_order_star_bad_width=7,
                graph_order_star_optimal_width=1,
                graph_order_bipartite_greedy_width=4,
                graph_order_bipartite_optimal_width=2,
                variable_boundary_cases=5,variable_boundary_chain_64_width=1,
                variable_boundary_star_bad_width=11,variable_boundary_star_good_width=1,
                variable_boundary_exhaustive_cnfs=2952,
                variable_boundary_exhaustive_certificates=17712,
                variable_boundary_redundancy_cases=6,
                variable_boundary_redundancy_largest_raw_states=766,
                variable_boundary_redundancy_largest_normalized_states=25,
                primal_order_cases=6,primal_order_exact=5,primal_order_unknown=1,
                primal_order_chain_width=1,primal_order_complete_width=5,
                row_basis_oracle_cases=11,row_basis_oracle_exact=10,
                row_basis_oracle_unknown=1,row_basis_trap_exact=[1,1,31],
                row_basis_oracle_trap_heuristic=[2,2,33],
                row_basis_oracle_rank_tradeoff_q=[2,2,28],
                row_basis_oracle_rank_tradeoff_p=[1,4,4,31],
                row_basis_oracle_rank_tradeoff_native_states=[4,2],
                row_basis_oracle_rank_tradeoff_native_distance=2,
                row_basis_oracle_rank_aware_objective=[1,4,4,31],
                row_basis_oracle_rank_aware_state_count=2,
                row_basis_rank5_cases=4,row_basis_rank5_group_size=9999360,
                row_basis_rank5_tradeoff_states=[4,2],
                row_basis_rank5_tradeoff_distance=2,
                comparison_exact={'stress22':11,'original58':54},
                comparison_unknown={'stress22':11,'original58':4},
                comparison_recognition_attempts=comparison['recognition_attempts'],
                comparison_recognition_rejections=comparison['recognition_rejections'],
                hashes=hashes,
                scope='Fresh hashes and saved status/arithmetic consistency; expensive solver searches are represented by explicitly bound run records. No P-versus-NP resolution claim.')
    (HERE/'FOLLOWUP_ARTIFACT_AUDIT.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps({k:output[k] for k in ('status','files','unit_tests','comparison_cases','comparison_recognition_rejections')}))


if __name__=='__main__': main()
