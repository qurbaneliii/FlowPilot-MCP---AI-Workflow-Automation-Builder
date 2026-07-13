# Test Traceability

This document maps major product requirements to concrete test coverage. It is not a full pytest inventory; it highlights the tests that prove the MVP acceptance criteria.

## Backend API and E2E Flow

| Requirement | Test coverage |
|---|---|
| `/api/v1/health` works | `test_health_endpoint_still_passes`, `test_health_response_contains_ui_status_labels` |
| `/api/v1/workflows/generate` works | `test_generate_workflow_success` |
| Invalid repo URL is structured | `test_generate_workflow_invalid_repo_url`, `test_structured_error_contains_severity_and_retryable` |
| Workflow generation returns UI summary/display data | `test_generate_workflow_response_contains_summary_and_node_display` |
| Workflow retrieval works | `test_get_workflow_success` |
| `/api/v1/workflows/run` creates run state | `test_run_workflow_starts_and_creates_run` |
| `/api/v1/runs/{run_id}` returns node status | `test_get_run_returns_node_statuses` |
| Run response contains summary, timeline, UI state | `test_run_response_contains_summary_timeline_and_ui_state` |
| Waiting for approval recommends approval view | `test_run_response_waiting_for_approval_recommends_approval_view` |
| Completed run recommends reports view | `test_run_response_completed_recommends_reports_view` |
| Issue creator is not marked completed before approval | `test_run_response_status_mapping_does_not_mark_pending_issue_creator_completed_before_approval` |
| Approval approve resumes run | `test_approve_resumes_run` |
| Approval reject skips issue creator | `test_reject_skips_issue_creator` |
| Duplicate approval controlled | `test_approve_double_call_controlled` |
| Artifacts are returned | `test_artifacts_appear_in_run_response` |
| Artifact tabs avoid contradictory empty state | `test_artifact_tabs_do_not_show_empty_when_artifact_exists` |
| Approval responses include frontend hints | `test_approval_response_contains_frontend_message_and_poll_hint` |
| Full backend GitHub audit flow | `test_backend_e2e_github_repo_audit_approval_completion` |

## Workflow Engine

| Requirement | Test coverage |
|---|---|
| Linear, diamond, disconnected topological sort | `test_topological_sort_linear_chain`, `test_topological_sort_diamond_dependency`, `test_topological_sort_disconnected_subgraphs` |
| Deterministic ordering | `test_topological_sort_deterministic_tie_break` |
| Cycle and dangling dependency rejection | `test_cycle_detection_*`, `test_dangling_dependency_reference_raises` |
| Duplicate node id rejection | `test_duplicate_node_id_raises` |
| Human approval pause/resume/reject | `test_human_approval_pauses_run_and_returns_control`, `test_resume_after_approval_continues_remaining_nodes`, `test_resume_after_rejection_skips_downstream_and_fails_run` |
| Retry/timeout behavior | `test_flaky_handler_succeeds_after_retries`, `test_retry_exhausted_after_max_attempts_marks_node_failed`, `test_slow_handler_times_out` |
| Workflow package boundary | `test_workflow_package_has_no_fastapi_import`, `test_workflow_package_has_no_sqlalchemy_import`, `test_workflow_package_has_no_infrastructure_layer_import` |

## Agent Layer

| Requirement | Test coverage |
|---|---|
| Real mode without API key fails clearly | `test_agent_not_configured_without_api_key` |
| Valid output accepted | `test_agent_returns_valid_output_on_first_response` |
| Invalid output reprompted once | `test_agent_reprompts_once_on_invalid_response_then_succeeds` |
| Second invalid output fails | `test_agent_fails_after_second_invalid_response` |
| Transient retry | `test_agent_retries_on_transient_error_then_succeeds` |
| Permanent errors not retried | `test_agent_does_not_retry_permanent_error` |
| Planner uses registered node types | `test_planner_uses_current_node_registry_types_not_hardcoded_list` |
| Validator catches unsafe write without approval | `test_validator_detects_unsafe_write_without_approval` |
| Schemas enforce categories, scores, priorities, publish claims | `test_repo_analyzer_output_schema_rejects_invalid_category`, `test_readme_reviewer_score_bounds_are_enforced`, `test_issue_generator_rejects_invalid_priority`, `test_linkedin_draft_agent_does_not_claim_publish_action` |
| Prompts are versioned and non-placeholder | `test_agent_prompt_files_are_not_placeholders` |

## MCP Layer

| Requirement | Test coverage |
|---|---|
| GitHub mock snapshot | `test_github_client_mock_returns_realistic_snapshot` |
| GitHub mock idempotent issue creation | `test_github_client_mock_create_issue_idempotent_on_same_key` |
| Real GitHub REST read contract and controlled failures | `test_real_github_url_parser`, `test_github_reader_public_repo_snapshot_contract`, `test_github_reader_missing_readme_is_not_failure`, `test_github_reader_provider_errors_are_controlled` |
| Real issue token gate and idempotency | `test_issue_creator_real_mode_requires_token`, `test_issue_creator_real_mode_is_idempotent` |
| Filesystem mock reads fixture tree | `test_filesystem_client_mock_reads_fixture_tree` |
| OpenAI MCP unavailable mode | `test_openai_mcp_client_unavailable_mode_when_url_unset`, `test_openai_mcp_client_call_tool_raises_when_unavailable` |
| Fake MCP server handshake | `test_openai_mcp_client_handshake_against_fake_server` |
| Registry mode selection | `test_registry_resolves_mock_by_default_without_mode_env`, `test_registry_resolves_real_when_mode_env_set_to_real` |
| Port contract | `test_tool_client_port_contract_satisfied_by_all_concrete_clients` |

## Node Handlers

| Requirement | Test coverage |
|---|---|
| All production handlers exist and run | `test_manual_trigger_success`, `test_github_repo_reader_success_mock`, `test_repo_analyzer_success`, `test_readme_reviewer_success`, `test_issue_draft_generator_success`, `test_human_approval_pauses`, `test_github_issue_creator_requires_approval`, `test_linkedin_draft_generator_success`, `test_markdown_report_writer_persists_artifacts` |
| GitHub issue creator requires approval | `test_github_issue_creator_requires_approval`, `test_github_issue_creator_rejects_missing_approval`, `test_github_issue_creator_rejects_rejected_approval` |
| GitHub issue creator idempotency and mock mode | `test_github_issue_creator_idempotency`, `test_github_issue_creator_mock_mode_explicit` |
| LinkedIn node never publishes | `test_linkedin_draft_generator_never_publishes` |
| Condition node safety | `test_condition_rejects_function_calls`, `test_condition_rejects_attribute_access`, `test_condition_rejects_imports`, `test_condition_rejects_unsafe_builtins`, `test_condition_resolves_names_only_from_context` |
| Raw exceptions become controlled failures | `test_raw_agent_exception_converted_to_failed_result`, `test_raw_mcp_exception_converted_to_failed_result` |
| Example workflow uses registered node types | `test_example_workflow_uses_only_registered_node_types` |

## Persistence Layer

The SQLAlchemy persistence layer has integration tests for:

- workflow create/load round trip
- run state round trip
- optimistic concurrency conflict
- approval double-resolve race
- approval rejection cascaded skips
- artifact save/list
- migration upgrade idempotency
- full engine run persisted end to end
- runtime storage selection and service-reload persistence for runs, approvals, and artifacts

These tests require a reachable PostgreSQL test database and are skipped in local runs when no test database is available.

Local runs without `TEST_DATABASE_URL` or `DATABASE_URL` skip 13 Postgres integration tests with the reason `No TEST_DATABASE_URL or DATABASE_URL configured for Postgres tests`.

CI provides a PostgreSQL service container, creates `flowpilot_test`, runs Alembic migrations against `TEST_DATABASE_URL`, and treats any skipped integration test as a CI failure. This prevents Postgres integration coverage from passing silently when the service is unreachable.

## Frontend Checks

Frontend quality is verified with:

```powershell
cd frontend
npm run typecheck
npm run lint
npm run build
```

Current code includes typed API models for health, workflow, run, approval, artifacts, structured errors, and backend-driven UI state.

The 2026-07-13 visual acceptance pass exercised the local browser flow at 1440px, 1366px, 1280px, and 1024px and refreshed the five screenshots under `docs/screenshots/`.

## Stack Verification

Docker verification is performed with:

```powershell
docker info
docker compose config --quiet
.\scripts\verify_stack.ps1
```

If Docker is unavailable, report that explicitly rather than claiming stack verification.

Final local hardening on 2026-07-13: Docker Desktop did not become responsive during a bounded startup attempt, while `docker compose config --quiet` passed. The full Docker stack and local Postgres test run were therefore not runtime-verified on this host; CI must execute the Postgres tests without skips.
