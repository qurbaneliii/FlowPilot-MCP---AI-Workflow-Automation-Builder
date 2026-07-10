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

## Phase 4 Agent Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | Agent fails clearly when real mode has no API key | `test_agent_not_configured_without_api_key` | Passing |
| 2 | Agent returns valid output on first backend response | `test_agent_returns_valid_output_on_first_response` | Passing |
| 3 | Agent reprompts once after invalid response and then succeeds | `test_agent_reprompts_once_on_invalid_response_then_succeeds` | Passing |
| 4 | Agent fails after second invalid response | `test_agent_fails_after_second_invalid_response` | Passing |
| 5 | Agent retries transient backend errors | `test_agent_retries_on_transient_error_then_succeeds` | Passing |
| 6 | Agent does not retry permanent backend errors | `test_agent_does_not_retry_permanent_error` | Passing |
| 7 | Planner uses current node registry types | `test_planner_uses_current_node_registry_types_not_hardcoded_list` | Passing |
| 8 | Planner controls unsupported MVP use cases | `test_planner_rejects_or_controls_unsupported_use_case` | Passing |
| 9 | Validator runs deterministic domain checks before backend call | `test_validator_pre_checks_with_domain_validate_and_sort_before_llm_call` | Passing |
| 10 | Validator detects unsafe write without approval | `test_validator_detects_unsafe_write_without_approval` | Passing |
| 11 | Repo analyzer schema rejects invalid category | `test_repo_analyzer_output_schema_rejects_invalid_category` | Passing |
| 12 | README reviewer score bounds are enforced | `test_readme_reviewer_score_bounds_are_enforced` | Passing |
| 13 | Issue generator rejects invalid priority | `test_issue_generator_rejects_invalid_priority` | Passing |
| 14 | LinkedIn draft schema rejects publish claims | `test_linkedin_draft_agent_does_not_claim_publish_action` | Passing |
| 15 | Agent prompt files are versioned and non-placeholder | `test_agent_prompt_files_are_not_placeholders` | Passing |
| 16 | Agent output schemas reject extra fields | `test_agent_output_schemas_reject_extra_fields_where_appropriate` | Passing |

## Phase 5 Production Node Handler Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | Manual trigger success | `test_manual_trigger_success` | Passing |
| 2 | GitHub repo reader mock success | `test_github_repo_reader_success_mock` | Passing |
| 3 | GitHub repo reader failure controlled | `test_github_repo_reader_failure_becomes_node_failure` | Passing |
| 4 | GitHub repo reader timeout controlled | `test_github_repo_reader_timeout_becomes_node_failure` | Passing |
| 5 | Repo analyzer success | `test_repo_analyzer_success` | Passing |
| 6 | Repo analyzer validation failure controlled | `test_repo_analyzer_agent_validation_failure_becomes_node_failure` | Passing |
| 7 | README reviewer success | `test_readme_reviewer_success` | Passing |
| 8 | Missing README handled | `test_readme_reviewer_missing_readme` | Passing |
| 9 | Issue draft generation success | `test_issue_draft_generator_success` | Passing |
| 10 | Zero findings returns empty issues | `test_issue_draft_generator_zero_findings` | Passing |
| 11 | Human approval pauses | `test_human_approval_pauses` | Passing |
| 12 | Human approval request contains record payload | `test_human_approval_creates_approval_record` | Passing |
| 13 | Issue creator requires approval | `test_github_issue_creator_requires_approval` | Passing |
| 14 | Issue creator rejects missing approval | `test_github_issue_creator_rejects_missing_approval` | Passing |
| 15 | Issue creator rejects rejected approval | `test_github_issue_creator_rejects_rejected_approval` | Passing |
| 16 | Issue creator idempotency | `test_github_issue_creator_idempotency` | Passing |
| 17 | Issue creator mock mode explicit | `test_github_issue_creator_mock_mode_explicit` | Passing |
| 18 | LinkedIn draft generation success | `test_linkedin_draft_generator_success` | Passing |
| 19 | LinkedIn node never publishes | `test_linkedin_draft_generator_never_publishes` | Passing |
| 20 | Markdown report artifacts emitted | `test_markdown_report_writer_persists_artifacts` | Passing |
| 21 | Condition true branch | `test_condition_true_branch` | Passing |
| 22 | Condition false branch | `test_condition_false_branch` | Passing |
| 23 | Function calls rejected | `test_condition_rejects_function_calls` | Passing |
| 24 | Attribute access rejected | `test_condition_rejects_attribute_access` | Passing |
| 25 | Imports rejected | `test_condition_rejects_imports` | Passing |
| 26 | Unsafe builtins rejected | `test_condition_rejects_unsafe_builtins` | Passing |
| 27 | Names resolve only from context | `test_condition_resolves_names_only_from_context` | Passing |
| 28 | Raw agent exception sanitized | `test_raw_agent_exception_converted_to_failed_result` | Passing |
| 29 | Raw MCP exception sanitized | `test_raw_mcp_exception_converted_to_failed_result` | Passing |
| 30 | Example workflow uses registered types | `test_example_workflow_uses_only_registered_node_types` | Passing |

## Phase 6 API and Backend E2E Matrix

| ID | Required behavior | Test function | Status |
|---|---|---|---|
| 1 | Generate workflow success | `test_generate_workflow_success` | Passing |
| 2 | Invalid GitHub URL rejected | `test_generate_workflow_invalid_repo_url` | Passing |
| 3 | Validation failure structured | `test_generate_workflow_validation_failure` | Passing |
| 4 | Get workflow success | `test_get_workflow_success` | Passing |
| 5 | Missing workflow returns 404 | `test_get_missing_workflow_returns_404` | Passing |
| 6 | Run workflow creates run | `test_run_workflow_starts_and_creates_run` | Passing |
| 7 | Get run returns node statuses | `test_get_run_returns_node_statuses` | Passing |
| 8 | Run pauses at approval | `test_run_pauses_at_approval` | Passing |
| 9 | Approve resumes run | `test_approve_resumes_run` | Passing |
| 10 | Reject skips issue creator | `test_reject_skips_issue_creator` | Passing |
| 11 | Double approve controlled | `test_approve_double_call_controlled` | Passing |
| 12 | Artifacts appear in run response | `test_artifacts_appear_in_run_response` | Passing |
| 13 | Route handlers are thin | `test_route_handlers_are_thin` | Passing |
| 14 | API errors are structured | `test_api_errors_are_structured` | Passing |
| 15 | Health endpoint still passes | `test_health_endpoint_still_passes` | Passing |
| 16 | Full backend E2E approval completion | `test_backend_e2e_github_repo_audit_approval_completion` | Passing |
