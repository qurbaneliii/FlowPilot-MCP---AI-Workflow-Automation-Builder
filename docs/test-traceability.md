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
| 1 | Workflow create/load round trip | `test_create_and_load_workflow_roundtrip` | Passing against native Postgres |
| 2 | Run creation initializes pending nodes | `test_create_run_initializes_all_node_execution_rows_pending` | Passing against native Postgres |
| 3 | Save/reload run state round trip | `test_save_and_reload_run_state_roundtrip` | Passing against native Postgres |
| 4 | Optimistic concurrency stale save conflict | `test_optimistic_concurrency_conflict_on_stale_save` | Passing against native Postgres |
| 5 | Approval double-resolve race | `test_approval_double_resolve_race_only_one_succeeds` | Passing against native Postgres |
| 6 | Approval rejection persists cascaded skips | `test_approval_reject_persists_cascaded_skips_correctly` | Passing against native Postgres |
| 7 | Artifact save/list | `test_artifact_save_and_list_for_run` | Passing against native Postgres |
| 8 | Node execution uniqueness | `test_unique_constraint_prevents_duplicate_node_execution_row` | Passing against native Postgres |
| 9 | Migration upgrade head idempotency | `test_migration_upgrade_head_idempotent` | Passing against native Postgres |
| 10 | Engine run persisted end to end | `test_full_engine_run_persisted_end_to_end` | Passing against native Postgres |

## Phase 3 MCP Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | GitHub mock returns realistic snapshot | `test_github_client_mock_returns_realistic_snapshot` | Passing |
| 2 | GitHub mock idempotent same key | `test_github_client_mock_create_issue_idempotent_on_same_key` | Passing |
| 3 | GitHub mock distinct keys create distinct URLs | `test_github_client_mock_create_issue_distinct_for_different_keys` | Passing |
| 4 | Filesystem mock reads fixture tree | `test_filesystem_client_mock_reads_fixture_tree` | Passing |
| 5 | OpenAI MCP unavailable mode when URL unset | `test_openai_mcp_client_unavailable_mode_when_url_unset` | Passing |
| 6 | OpenAI MCP unavailable warning logs once | `test_openai_mcp_client_unavailable_mode_logs_warning_once` | Passing |
| 7 | OpenAI MCP unavailable call raises | `test_openai_mcp_client_call_tool_raises_when_unavailable` | Passing |
| 8 | OpenAI MCP handshake against fake server | `test_openai_mcp_client_handshake_against_fake_server` | Passing |
| 9 | OpenAI MCP list tools reflects server tools | `test_openai_mcp_client_list_tools_reflects_server_advertised_tools` | Passing |
| 10 | Registry defaults to mock clients | `test_registry_resolves_mock_by_default_without_mode_env` | Passing |
| 11 | Registry resolves real clients when mode set | `test_registry_resolves_real_when_mode_env_set_to_real` | Passing |
| 12 | Registry unknown client raises | `test_registry_unknown_client_name_raises` | Passing |
| 13 | ToolClientPort contract satisfied by clients | `test_tool_client_port_contract_satisfied_by_all_concrete_clients` | Passing |
| E1 | Registry is sole mode-branching point | `test_registry_is_sole_mode_branching_point` | Passing |
