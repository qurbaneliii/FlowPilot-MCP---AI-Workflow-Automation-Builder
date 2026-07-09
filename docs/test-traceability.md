# Test Traceability

This document maps specification-required test items to concrete test functions.

## Phase 1 Required Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | Linear topological sort | `test_topological_sort_linear_chain` | Passing |
| 2 | Diamond dependency sort | `test_topological_sort_diamond_dependency` | Passing |
| 3 | Disconnected subgraph sort | `test_topological_sort_disconnected_subgraphs` | Passing |
| 4 | Deterministic tie break | `test_topological_sort_deterministic_tie_break` | Passing |
| 5 | Two-node cycle detection | `test_cycle_detection_simple_two_node_cycle` | Passing |
| 6 | Self-loop cycle detection | `test_cycle_detection_self_loop` | Passing |
| 7 | Long indirect cycle detection | `test_cycle_detection_long_indirect_cycle` | Passing |
| 8 | Cycle path reporting | `test_cycle_error_reports_correct_path` | Passing |
| 9 | Dangling dependency detection | `test_dangling_dependency_reference_raises` | Passing |
| 10 | Duplicate node id detection | `test_duplicate_node_id_raises` | Passing |
| 11 | Empty graph order | `test_empty_graph_returns_empty_order` | Passing |
| 12 | Single node order | `test_single_node_no_dependencies` | Passing |
| 13 | Register and retrieve handler | `test_register_and_retrieve_handler` | Passing |
| 14 | Duplicate registration fails fast | `test_duplicate_registration_raises_at_registration_time` | Passing |
| 15 | Unknown node type lookup | `test_unknown_node_type_raises_on_lookup` | Passing |
| 16 | Valid pending to running transition | `test_valid_transition_pending_to_running` | Passing |
| 17 | Invalid completed to running transition | `test_invalid_transition_completed_to_running_raises` | Passing |
| 18 | Terminal statuses reject transitions | `test_all_terminal_statuses_reject_further_transitions` | Passing |
| 19 | Full success path | `test_full_success_path_all_nodes_complete` | Passing |
| 20 | Failure cascades downstream | `test_failure_cascades_downstream_to_skipped` | Passing |
| 21 | Independent branch survives sibling failure | `test_failure_does_not_affect_independent_branch` | Passing |
| 22 | Human approval pauses run | `test_human_approval_pauses_run_and_returns_control` | Passing |
| 23 | Approval resume continues run | `test_resume_after_approval_continues_remaining_nodes` | Passing |
| 24 | Rejection skips downstream and fails run | `test_resume_after_rejection_skips_downstream_and_fails_run` | Passing |
| 25 | Invalid resume state raises | `test_resume_on_non_waiting_node_raises_invalid_resume_state` | Passing |
| 26 | Flaky handler succeeds after retry | `test_flaky_handler_succeeds_after_retries` | Passing |
| 27 | Retry exhaustion marks node failed | `test_retry_exhausted_after_max_attempts_marks_node_failed` | Passing |
| 28 | Permanent error is not retried | `test_permanent_error_does_not_retry` | Passing |
| 29 | Slow handler times out | `test_slow_handler_times_out` | Passing |
| 30 | Timeout is retried then fails run | `test_timeout_retried_and_eventually_fails_run` | Passing |
| 31 | No FastAPI import in workflow package | `test_workflow_package_has_no_fastapi_import` | Passing |
| 32 | No SQLAlchemy import in workflow package | `test_workflow_package_has_no_sqlalchemy_import` | Passing |
| 33 | No infrastructure import in workflow package | `test_workflow_package_has_no_infrastructure_layer_import` | Passing |

## Phase 1 Extra Coverage

| Extra | Behavior | Test function | Status |
|---|---|---|---|
| E1 | Direct status assignment guard | `test_node_status_assignment_only_occurs_inside_transition_method` | Passing |
| E2 | RunState JSON round trip | `test_run_state_json_round_trip_preserves_value` | Passing |
| E3 | DB health reachable branch | `test_check_database_returns_ok_when_query_succeeds` | Passing |
| E4 | DB health unreachable branch | `test_check_database_returns_error_when_query_fails` | Passing |
| E5 | OpenAI not configured branch | `test_check_openai_returns_not_configured_without_key` | Passing |
| E6 | OpenAI configured branch | `test_check_openai_returns_ok_with_key` | Passing |
| E7 | Health endpoint degraded dependency response | `test_health_endpoint_returns_200_when_dependencies_degraded` | Passing |
| E8 | Health endpoint healthy dependency response | `test_health_endpoint_returns_200_when_dependencies_healthy` | Passing |
| E9 | Terminal transition rejection covers completed | `test_all_terminal_statuses_reject_further_transitions[COMPLETED]` | Passing |
| E10 | Terminal transition rejection covers failed | `test_all_terminal_statuses_reject_further_transitions[FAILED]` | Passing |

## Phase 2 Integration Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | Workflow create/load round trip | `test_create_and_load_workflow_roundtrip` | Written; local run skipped without Postgres |
| 2 | Run creation initializes pending nodes | `test_create_run_initializes_all_node_execution_rows_pending` | Written; local run skipped without Postgres |
| 3 | Save/reload run state round trip | `test_save_and_reload_run_state_roundtrip` | Written; local run skipped without Postgres |
| 4 | Optimistic concurrency stale save conflict | `test_optimistic_concurrency_conflict_on_stale_save` | Written; local run skipped without Postgres |
| 5 | Approval double-resolve race | `test_approval_double_resolve_race_only_one_succeeds` | Written; local run skipped without Postgres |
| 6 | Approval rejection persists cascaded skips | `test_approval_reject_persists_cascaded_skips_correctly` | Written; local run skipped without Postgres |
| 7 | Artifact save/list | `test_artifact_save_and_list_for_run` | Written; local run skipped without Postgres |
| 8 | Node execution uniqueness | `test_unique_constraint_prevents_duplicate_node_execution_row` | Written; local run skipped without Postgres |
| 9 | Migration upgrade head idempotency | `test_migration_upgrade_head_idempotent` | Written; local run skipped without Postgres |
| 10 | Engine run persisted end to end | `test_full_engine_run_persisted_end_to_end` | Written; local run skipped without Postgres |
