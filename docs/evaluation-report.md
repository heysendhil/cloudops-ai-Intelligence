# Phase 21 Evaluation Report -- Cloud Ops AI Intelligence

Generated 2026-09-14 00:13 by `scripts/generate_evaluation_report.py` directly from the pytest and vitest JUnit XML output of a full suite run. Every test below is either PASS, FAIL, or SKIP as reported by the test runner -- none are hidden, hand-edited, or simulated.

## Overall summary

- Backend (pytest): 400 total -- 331 passed, 69 failed, 0 skipped
- Frontend (vitest): 12 total -- 12 passed, 0 failed, 0 skipped
- **Combined: 412 total -- 343 passed, 69 failed, 0 skipped**

**69 FAILING TEST(S) -- see below. Not hidden.**

- 69 fail with the exact same root cause: Google's free-tier daily quota for this API key (`GenerateRequestsPerDayPerProjectPerModel-FreeTier`, 20 requests/day/model) was exhausted partway through this run. This is an external account-tier limit, not a code defect -- the same tests pass when quota is available (see the per-module isolated runs recorded during this evaluation). Every quota-blocked test is still listed individually below with its real status; none are hidden or converted to a fake PASS.


## 1-11. Evaluation by required category

Per CLAUDE.md's Agent/Task/Crew/Flow layering, a single test module often legitimately covers more than one category (e.g. an agent test module also builds and asserts on that agent's Task). Each test is still only counted once overall in the combined summary above; below it is shown once per category it actually exercises.

### 1. Tools

69 total -- 69 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_cloud_metrics_tool::test_tool_default_path_reads_the_real_incident_metrics` | PASS |  |
| `tests.test_cloud_metrics_tool::test_tool_is_a_crewai_basetool` | PASS |  |
| `tests.test_cloud_metrics_tool::test_tool_run_extracts_exact_values` | PASS |  |
| `tests.test_cloud_metrics_tool::test_tool_run_never_invents_missing_metrics` | PASS |  |
| `tests.test_cloud_metrics_tool::test_tool_run_returns_all_ten_requested_metrics` | PASS |  |
| `tests.test_cloud_metrics_tool::test_tool_run_works_without_any_llm_configured` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_default_runbooks_dir_reads_the_real_runbook` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_is_a_crewai_basetool` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_never_claims_llm_use_for_results` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_never_invents_content` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_results_include_source_references` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_returns_query_and_results` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_works_without_any_extra_llm_configured` | PASS |  |
| `tests.test_kubernetes_parser::test_available_replicas_exact_value` | PASS |  |
| `tests.test_kubernetes_parser::test_desired_replicas_exact_value` | PASS |  |
| `tests.test_kubernetes_parser::test_desired_replicas_missing_field_is_unavailable_not_invented` | PASS |  |
| `tests.test_kubernetes_parser::test_events_are_returned_verbatim` | PASS |  |
| `tests.test_kubernetes_parser::test_events_empty_when_not_present` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_include_probe_config` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_never_invent_events_for_healthy_pods` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_one_per_pod` | PASS |  |
| `tests.test_kubernetes_parser::test_missing_kubernetes_file_raises_file_not_found` | PASS |  |
| `tests.test_kubernetes_parser::test_pod_restart_counts_exact_values` | PASS |  |
| `tests.test_kubernetes_parser::test_pod_status_exact_values` | PASS |  |
| `tests.test_kubernetes_parser::test_ready_replicas_is_computed_from_pods` | PASS |  |
| `tests.test_kubernetes_parser::test_ready_replicas_unavailable_when_no_pods` | PASS |  |
| `tests.test_kubernetes_parser::test_real_incident_kubernetes_exact_values` | PASS |  |
| `tests.test_kubernetes_parser::test_real_incident_kubernetes_health_probe_findings` | PASS |  |
| `tests.test_kubernetes_parser::test_result_to_dict_is_json_serializable` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_default_path_reads_the_real_incident_kubernetes_state` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_is_a_crewai_basetool` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_never_claims_a_real_cluster_connection` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_run_extracts_exact_values` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_run_returns_all_required_sections` | PASS |  |
| `tests.test_kubernetes_reliability_tool::test_tool_run_works_without_any_llm_configured` | PASS |  |
| `tests.test_log_analysis_tool::test_tool_default_log_path_reads_the_real_incident_log` | PASS |  |
| `tests.test_log_analysis_tool::test_tool_is_a_crewai_basetool` | PASS |  |
| `tests.test_log_analysis_tool::test_tool_run_applies_time_window_and_min_occurrences` | PASS |  |
| `tests.test_log_analysis_tool::test_tool_run_returns_expected_structure` | PASS |  |
| `tests.test_log_analysis_tool::test_tool_run_works_without_any_llm_configured` | PASS |  |
| `tests.test_log_parser::test_empty_log_file_yields_no_entries_not_fabricated_ones` | PASS |  |
| `tests.test_log_parser::test_extracts_sorted_unique_timestamps` | PASS |  |
| `tests.test_log_parser::test_filters_to_incident_timeframe` | PASS |  |
| `tests.test_log_parser::test_identifies_error_entries` | PASS |  |
| `tests.test_log_parser::test_identifies_repeated_patterns_with_normalization` | PASS |  |
| `tests.test_log_parser::test_identifies_warn_entries` | PASS |  |
| `tests.test_log_parser::test_min_pattern_occurrences_threshold_is_respected` | PASS |  |
| `tests.test_log_parser::test_missing_log_file_raises_file_not_found` | PASS |  |
| `tests.test_log_parser::test_never_invents_entries_not_present_in_file` | PASS |  |
| `tests.test_log_parser::test_parse_entries_extracts_structured_fields` | PASS |  |
| `tests.test_log_parser::test_raw_line_is_exact_evidence_reference` | PASS |  |
| `tests.test_log_parser::test_result_to_dict_is_json_serializable` | PASS |  |
| `tests.test_metrics_parser::test_active_connections_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_application_cpu_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_application_memory_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_connection_limit_exact_value` | PASS |  |
| `tests.test_metrics_parser::test_database_connections_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_database_cpu_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_database_memory_is_reported_as_unavailable_not_invented` | PASS |  |
| `tests.test_metrics_parser::test_http_5xx_percentage_is_computed_exactly` | PASS |  |
| `tests.test_metrics_parser::test_missing_connection_limit_is_reported_as_unavailable` | PASS |  |
| `tests.test_metrics_parser::test_missing_field_across_empty_datapoints_is_unavailable` | PASS |  |
| `tests.test_metrics_parser::test_missing_metrics_file_raises_file_not_found` | PASS |  |
| `tests.test_metrics_parser::test_query_latency_is_reported_as_unavailable_not_invented` | PASS |  |
| `tests.test_metrics_parser::test_real_incident_data_has_no_db_memory_or_query_latency` | PASS |  |
| `tests.test_metrics_parser::test_real_incident_metrics_baseline_values` | PASS |  |
| `tests.test_metrics_parser::test_real_incident_metrics_exact_peak_values` | PASS |  |
| `tests.test_metrics_parser::test_request_latency_exact_values` | PASS |  |
| `tests.test_metrics_parser::test_result_to_dict_is_json_serializable` | PASS |  |

### 2. Agents

110 total -- 110 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_backstory_states_grounding_and_distinction_constraints` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_uses_cloud_metrics_tool` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_observed_fact_schema_supports_traceability_and_relationship` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_references_custom_metrics_path` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_requires_observed_interpretation_cause_distinction` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_uses_cloud_metrics_tool` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_backstory_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_incident_reporter_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_incident_reporter_agent::test_default_incident_metadata_matches_the_real_incident_record` | PASS |  |
| `tests.test_incident_reporter_agent::test_remediation_recommendations_reuse_the_exact_recommendation_schema` | PASS |  |
| `tests.test_incident_reporter_agent::test_report_schema_has_exactly_the_fourteen_requested_fields` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_all_six_upstream_reports_verbatim` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_incident_metadata` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_altering_remediation_recommendations` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_incident_reporter_agent::test_timeline_entry_schema_supports_source_attribution` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_backstory_covers_all_five_required_behaviors` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_goal_distinguishes_knowledge_from_evidence` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_uses_knowledge_retrieval_tool` | PASS |  |
| `tests.test_knowledge_rag_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_knowledge_rag_agent::test_cited_knowledge_chunk_schema_supports_source_citation_and_distinction` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_includes_incident_id_and_query` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_requires_respecting_production_safety` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_requires_source_citation_and_separation` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_uses_knowledge_retrieval_tool` | PASS |  |
| `tests.test_knowledge_rag_agent::test_troubleshooting_procedure_schema_requires_safety_note` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_backstory_forbids_assuming_kubernetes_is_root_cause` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_goal_covers_health_and_root_cause_vs_consequence` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_uses_kubernetes_reliability_tool` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_root_cause_assessment_is_constrained_to_three_values` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_forbids_assuming_kubernetes_is_root_cause` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_references_custom_k8s_path` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_requires_all_five_determinations` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_uses_kubernetes_reliability_tool` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_backstory_states_grounding_constraint` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_uses_log_analysis_tool` | PASS |  |
| `tests.test_log_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_log_analyst_agent::test_default_task_window_matches_incident_record` | PASS |  |
| `tests.test_log_analyst_agent::test_task_description_includes_incident_and_window` | PASS |  |
| `tests.test_log_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_log_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_log_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_log_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_log_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_log_analyst_agent::test_task_uses_log_analysis_tool` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_backstory_covers_safety_and_grounding` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_goal_states_never_execute_and_human_approval` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_remediation_advisor_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_requires_human_approval_is_type_locked_to_true` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_schema_has_exactly_the_required_four_fields` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_embeds_rca_and_knowledge_verbatim` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_forbids_claiming_execution` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_lists_all_four_requirements` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_backstory_covers_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_goal_names_all_four_upstream_agents` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_embeds_all_four_upstream_reports_verbatim` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_lists_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |

### 3. Tasks

123 total -- 123 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_backstory_states_grounding_and_distinction_constraints` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_agent_uses_cloud_metrics_tool` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_observed_fact_schema_supports_traceability_and_relationship` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_references_custom_metrics_path` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_description_requires_observed_interpretation_cause_distinction` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_cloud_infrastructure_analyst_agent::test_task_uses_cloud_metrics_tool` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_backstory_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_incident_reporter_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_incident_reporter_agent::test_default_incident_metadata_matches_the_real_incident_record` | PASS |  |
| `tests.test_incident_reporter_agent::test_remediation_recommendations_reuse_the_exact_recommendation_schema` | PASS |  |
| `tests.test_incident_reporter_agent::test_report_schema_has_exactly_the_fourteen_requested_fields` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_all_six_upstream_reports_verbatim` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_incident_metadata` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_altering_remediation_recommendations` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_incident_reporter_agent::test_timeline_entry_schema_supports_source_attribution` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_backstory_covers_all_five_required_behaviors` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_goal_distinguishes_knowledge_from_evidence` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_knowledge_rag_agent::test_agent_uses_knowledge_retrieval_tool` | PASS |  |
| `tests.test_knowledge_rag_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_knowledge_rag_agent::test_cited_knowledge_chunk_schema_supports_source_citation_and_distinction` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_includes_incident_id_and_query` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_requires_respecting_production_safety` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_description_requires_source_citation_and_separation` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_knowledge_rag_agent::test_task_uses_knowledge_retrieval_tool` | PASS |  |
| `tests.test_knowledge_rag_agent::test_troubleshooting_procedure_schema_requires_safety_note` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_backstory_forbids_assuming_kubernetes_is_root_cause` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_goal_covers_health_and_root_cause_vs_consequence` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_agent_uses_kubernetes_reliability_tool` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_root_cause_assessment_is_constrained_to_three_values` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_forbids_assuming_kubernetes_is_root_cause` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_references_custom_k8s_path` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_description_requires_all_five_determinations` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_kubernetes_reliability_analyst_agent::test_task_uses_kubernetes_reliability_tool` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_backstory_states_grounding_constraint` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_log_analyst_agent::test_agent_uses_log_analysis_tool` | PASS |  |
| `tests.test_log_analyst_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_log_analyst_agent::test_default_task_window_matches_incident_record` | PASS |  |
| `tests.test_log_analyst_agent::test_task_description_includes_incident_and_window` | PASS |  |
| `tests.test_log_analyst_agent::test_task_description_references_tool_and_forbids_invention` | PASS |  |
| `tests.test_log_analyst_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_log_analyst_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_log_analyst_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_log_analyst_agent::test_task_output_pydantic_schema_has_exactly_required_fields` | PASS |  |
| `tests.test_log_analyst_agent::test_task_uses_log_analysis_tool` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_backstory_covers_safety_and_grounding` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_goal_states_never_execute_and_human_approval` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_remediation_advisor_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_requires_human_approval_is_type_locked_to_true` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_schema_has_exactly_the_required_four_fields` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_embeds_rca_and_knowledge_verbatim` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_forbids_claiming_execution` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_lists_all_four_requirements` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_backstory_covers_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_goal_names_all_four_upstream_agents` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_embeds_all_four_upstream_reports_verbatim` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_lists_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |
| `tests.test_root_cause_rubric::test_bad_report_scores_well_below_target` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_alternative_hypotheses_rejects_empty_list` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_alternative_hypotheses_rejects_hypothesis_identical_to_root_cause` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_confidence_calibrated_rejects_boundary_values` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_evidence_based_reasoning_rejects_unrecognized_source_agent` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_leading_hypothesis_justified_rejects_thin_justification` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_missing_evidence_rejects_empty_list` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_no_invented_metrics_flags_an_unknown_number` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_root_cause_not_just_symptoms_rejects_pure_symptom_restatement` | PASS |  |
| `tests.test_root_cause_rubric::test_good_report_scores_at_or_above_target` | PASS |  |
| `tests.test_root_cause_rubric::test_result_to_dict_is_json_serializable` | PASS |  |
| `tests.test_root_cause_rubric::test_rubric_has_seven_equally_weighted_criteria` | PASS |  |
| `tests.test_root_cause_rubric::test_single_failing_criterion_still_scores_near_but_below_full` | PASS |  |

### 4. Crew

17 total -- 17 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_api_incidents::test_crew_exception_is_handled_gracefully` | PASS |  |
| `tests.test_api_incidents::test_crew_returning_incomplete_report_is_handled` | PASS |  |
| `tests.test_crew::test_crew_accepts_custom_incident_metadata` | PASS |  |
| `tests.test_crew::test_crew_has_all_seven_agents_in_order` | PASS |  |
| `tests.test_crew::test_crew_has_all_seven_tasks_in_dependency_order` | PASS |  |
| `tests.test_crew::test_crew_name_constant` | PASS |  |
| `tests.test_crew::test_crew_uses_sequential_process` | PASS |  |
| `tests.test_crew::test_crew_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_crew::test_each_task_is_assigned_to_its_correct_agent` | PASS |  |
| `tests.test_crew::test_every_context_task_appears_earlier_in_the_crew_task_list` | PASS |  |
| `tests.test_crew::test_incident_report_task_context_is_all_six_upstream_tasks` | PASS |  |
| `tests.test_crew::test_remediation_task_context_is_root_cause_and_knowledge` | PASS |  |
| `tests.test_crew::test_root_cause_task_context_is_the_four_leaf_tasks` | PASS |  |
| `tests.test_crew::test_the_four_leaf_tasks_have_no_context` | PASS |  |
| `tests.test_flow::test_crew_raising_an_exception_is_handled_not_raised` | PASS |  |
| `tests.test_flow::test_crew_returning_incomplete_report_is_caught_by_evaluation` | PASS |  |
| `tests.test_flow::test_crew_returning_no_structured_output_is_handled` | PASS |  |

### 5. Flow

27 total -- 24 passed, 3 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation.test_flow_evaluation::test_flow_produces_a_complete_incident_report` | **FAIL** | assert None is not None |
| `tests.evaluation.test_flow_evaluation::test_flow_result_requires_human_approval` | **FAIL** | TypeError: 'NoneType' object is not subscriptable |
| `tests.evaluation.test_flow_evaluation::test_flow_succeeds_end_to_end` | **FAIL** | AssertionError: assert 'failed' == 'succeeded' |
| `tests.evaluation_suite.test_failure_scenarios::test_flow_handles_an_llm_timeout_gracefully` | PASS |  |
| `tests.test_flow::test_crew_raising_an_exception_is_handled_not_raised` | PASS |  |
| `tests.test_flow::test_crew_returning_incomplete_report_is_caught_by_evaluation` | PASS |  |
| `tests.test_flow::test_crew_returning_no_structured_output_is_handled` | PASS |  |
| `tests.test_flow::test_final_state_matches_the_returned_result` | PASS |  |
| `tests.test_flow::test_flow_module_has_no_remediation_execution_capability` | PASS |  |
| `tests.test_flow::test_load_incident_data_populates_state_from_the_real_record` | PASS |  |
| `tests.test_flow::test_missing_incident_id_fails_validation_without_invoking_crew` | PASS |  |
| `tests.test_flow::test_real_incident_data_is_loaded_from_disk` | PASS |  |
| `tests.test_flow::test_result_always_states_human_approval_is_required_even_on_failure` | PASS |  |
| `tests.test_flow::test_successful_investigation_against_inc_2026_0912` | PASS |  |
| `tests.test_flow::test_unknown_incident_id_fails_validation_without_invoking_crew` | PASS |  |
| `tests.test_flow::test_validate_incident_router_returns_invalid_for_unknown_incident` | PASS |  |
| `tests.test_flow::test_validate_incident_router_returns_valid_for_known_incident` | PASS |  |
| `tests.test_investigations::test_get_job_returns_none_for_unknown_job_id` | PASS |  |
| `tests.test_investigations::test_handlers_ignore_events_outside_any_job_context` | PASS |  |
| `tests.test_investigations::test_job_for_unknown_incident_becomes_invalid_with_all_tasks_still_pending` | PASS |  |
| `tests.test_investigations::test_job_reaches_succeeded_with_the_real_result` | PASS |  |
| `tests.test_investigations::test_on_task_completed_falls_back_to_raw_output_without_summary_or_root_cause` | PASS |  |
| `tests.test_investigations::test_on_task_completed_marks_completed_with_a_real_finding` | PASS |  |
| `tests.test_investigations::test_on_task_failed_marks_failed_with_the_real_error` | PASS |  |
| `tests.test_investigations::test_on_task_started_marks_the_matching_task_running` | PASS |  |
| `tests.test_investigations::test_start_investigation_returns_immediately_with_all_tasks_pending` | PASS |  |
| `tests.test_investigations::test_task_started_event_is_wired_through_the_real_event_bus` | PASS |  |

### 6. FastAPI

21 total -- 21 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_api_incidents::test_crew_exception_is_handled_gracefully` | PASS |  |
| `tests.test_api_incidents::test_crew_returning_incomplete_report_is_handled` | PASS |  |
| `tests.test_api_incidents::test_every_recommendation_in_the_response_requires_human_approval` | PASS |  |
| `tests.test_api_incidents::test_get_incident_summary_malformed_id_returns_422` | PASS |  |
| `tests.test_api_incidents::test_get_incident_summary_returns_real_incident_metadata` | PASS |  |
| `tests.test_api_incidents::test_get_incident_summary_unknown_incident_returns_404` | PASS |  |
| `tests.test_api_incidents::test_get_investigation_job_for_a_different_incident_id_returns_404` | PASS |  |
| `tests.test_api_incidents::test_incident_id_containing_a_path_separator_never_reaches_the_handler[../../etc/passwd]` | PASS |  |
| `tests.test_api_incidents::test_incident_id_containing_a_path_separator_never_reaches_the_handler[INC/2026/0912]` | PASS |  |
| `tests.test_api_incidents::test_malformed_incident_id_returns_422[INC 2026 0912]` | PASS |  |
| `tests.test_api_incidents::test_malformed_incident_id_returns_422[INC-2026-0912!!!]` | PASS |  |
| `tests.test_api_incidents::test_response_always_includes_a_status_field` | PASS |  |
| `tests.test_api_incidents::test_response_model_has_no_endpoint_for_executing_remediation` | PASS |  |
| `tests.test_api_incidents::test_secret_is_never_exposed_in_the_response` | PASS |  |
| `tests.test_api_incidents::test_successful_investigation_report_includes_all_required_sections` | PASS |  |
| `tests.test_api_incidents::test_successful_investigation_returns_200_with_full_report` | PASS |  |
| `tests.test_api_incidents::test_unknown_incident_returns_404` | PASS |  |
| `tests.test_health::test_health_returns_ok` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_include_probe_config` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_never_invent_events_for_healthy_pods` | PASS |  |
| `tests.test_kubernetes_parser::test_health_probe_findings_one_per_pod` | PASS |  |

### 7. Next.js integration

12 total -- 12 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `components/AgentWorkflow.test.tsx::AgentWorkflow > never renders a finding for a pending or running task, even if one were present in the data` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > renders all 7 agents by their display name` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > renders nothing extra for an empty task list` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > shows Running for a task currently in progress` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > shows a real finding only for a task that actually completed` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > shows every agent as Pending before anything has run, with no findings` | PASS |  |
| `components/AgentWorkflow.test.tsx::AgentWorkflow > shows the real error only for a task that actually failed` | PASS |  |
| `lib/api-client.test.ts::pollInvestigationJob > GETs the specific job and returns its current state` | PASS |  |
| `lib/api-client.test.ts::pollInvestigationJob > throws ApiError when the job is not found` | PASS |  |
| `lib/api-client.test.ts::startInvestigationJob > POSTs to the investigations endpoint and returns the job` | PASS |  |
| `lib/api-client.test.ts::startInvestigationJob > is an instance of ApiError specifically` | PASS |  |
| `lib/api-client.test.ts::startInvestigationJob > throws ApiError with the backend's detail message on failure` | PASS |  |

### 8. RAG

35 total -- 35 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_knowledge_retrieval_tool::test_tool_default_runbooks_dir_reads_the_real_runbook` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_is_a_crewai_basetool` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_never_claims_llm_use_for_results` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_never_invents_content` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_results_include_source_references` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_returns_query_and_results` | PASS |  |
| `tests.test_knowledge_retrieval_tool::test_tool_run_works_without_any_extra_llm_configured` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_ids_are_unique` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_markdown_empty_document_yields_no_chunks` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_markdown_extracts_document_title` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_markdown_falls_back_to_whole_document_without_h2_headings` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_markdown_splits_by_h2_headings` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_metadata_includes_source_path` | PASS |  |
| `tests.test_rag_ingestion::test_chunk_text_is_exact_substring_of_source_never_invented` | PASS |  |
| `tests.test_rag_ingestion::test_load_and_chunk_documents_covers_all_files` | PASS |  |
| `tests.test_rag_ingestion::test_load_markdown_documents_missing_directory_raises` | PASS |  |
| `tests.test_rag_ingestion::test_load_markdown_documents_reads_only_md_files` | PASS |  |
| `tests.test_rag_ingestion::test_load_markdown_documents_returns_exact_file_content` | PASS |  |
| `tests.test_rag_ingestion::test_load_markdown_documents_sorted_for_determinism` | PASS |  |
| `tests.test_rag_ingestion::test_real_runbook_chunk_text_is_verbatim_from_disk` | PASS |  |
| `tests.test_rag_ingestion::test_real_runbook_chunks_exactly_by_its_seven_sections` | PASS |  |
| `tests.test_rag_ingestion::test_real_runbook_directory_is_the_default` | PASS |  |
| `tests.test_rag_vector_store::test_build_runbook_collection_is_idempotent_on_a_persistent_client` | PASS |  |
| `tests.test_rag_vector_store::test_ingest_runbooks_adds_one_entry_per_chunk` | PASS |  |
| `tests.test_rag_vector_store::test_ingest_runbooks_empty_directory_adds_nothing` | PASS |  |
| `tests.test_rag_vector_store::test_ingest_runbooks_returns_the_chunks_it_added` | PASS |  |
| `tests.test_rag_vector_store::test_real_runbook_ingestion_and_retrieval_end_to_end` | PASS |  |
| `tests.test_rag_vector_store::test_real_runbook_retrieval_never_invents_content` | PASS |  |
| `tests.test_rag_vector_store::test_real_runbook_retrieval_returns_source_references` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_finds_the_semantically_relevant_chunk` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_on_empty_collection_returns_empty_list_not_error` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_orders_results_by_relevance` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_respects_n_results` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_returns_source_document_references` | PASS |  |
| `tests.test_rag_vector_store::test_retrieve_text_is_verbatim_from_the_source_file_never_invented` | PASS |  |

### 9. RCA (Root Cause Analysis)

30 total -- 27 passed, 3 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation.test_root_cause_investigator_evaluation::test_formal_rubric_score_meets_target` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_root_cause_investigator_evaluation::test_report_identifies_database_connection_pressure_as_root_cause` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_root_cause_investigator_evaluation::test_report_produces_a_root_cause` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.test_root_cause_investigator_agent::test_agent_backstory_covers_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_goal_names_all_four_upstream_agents` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_embeds_all_four_upstream_reports_verbatim` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_description_lists_all_seven_requirements` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_root_cause_investigator_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |
| `tests.test_root_cause_rubric::test_bad_report_scores_well_below_target` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_alternative_hypotheses_rejects_empty_list` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_alternative_hypotheses_rejects_hypothesis_identical_to_root_cause` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_confidence_calibrated_rejects_boundary_values` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_evidence_based_reasoning_rejects_unrecognized_source_agent` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_leading_hypothesis_justified_rejects_thin_justification` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_missing_evidence_rejects_empty_list` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_no_invented_metrics_flags_an_unknown_number` | PASS |  |
| `tests.test_root_cause_rubric::test_criterion_root_cause_not_just_symptoms_rejects_pure_symptom_restatement` | PASS |  |
| `tests.test_root_cause_rubric::test_good_report_scores_at_or_above_target` | PASS |  |
| `tests.test_root_cause_rubric::test_result_to_dict_is_json_serializable` | PASS |  |
| `tests.test_root_cause_rubric::test_rubric_has_seven_equally_weighted_criteria` | PASS |  |
| `tests.test_root_cause_rubric::test_single_failing_criterion_still_scores_near_but_below_full` | PASS |  |

### 10. Remediation safety

26 total -- 17 passed, 9 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation.test_remediation_advisor_evaluation::test_confidence_in_valid_range` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_every_recommendation_reason_overlaps_with_rca_or_runbook` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_every_recommendation_requires_human_approval` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_no_recommendation_claims_it_was_already_executed` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_produces_at_least_one_recommendation` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_recommendations_are_not_duplicated` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_recommendations_are_substantive_not_vague` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_safety_notice_states_advisory_only_and_human_approval` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_remediation_advisor_evaluation::test_summary_is_non_empty` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.test_remediation_advisor_agent::test_agent_backstory_covers_safety_and_grounding` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_goal_states_never_execute_and_human_approval` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_remediation_advisor_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_requires_human_approval_is_type_locked_to_true` | PASS |  |
| `tests.test_remediation_advisor_agent::test_recommendation_schema_has_exactly_the_required_four_fields` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_embeds_rca_and_knowledge_verbatim` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_forbids_claiming_execution` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_includes_incident_id` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_description_lists_all_four_requirements` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_remediation_advisor_agent::test_task_output_pydantic_schema_matches_exact_requested_shape` | PASS |  |

### 11. Reporter accuracy

28 total -- 17 passed, 11 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation.test_incident_reporter_evaluation::test_all_fourteen_sections_are_present_and_populated` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_cloud_findings_overlap_with_the_cloud_analyst_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_every_remediation_recommendation_still_requires_human_approval` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_human_approval_requirement_states_the_safety_property` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_incident_metadata_is_copied_exactly` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_kubernetes_findings_overlap_with_the_kubernetes_analyst_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_log_findings_overlap_with_the_log_analyst_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_relevant_runbook_overlaps_with_the_knowledge_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_remediation_recommendations_match_the_advisor_report_exactly` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_root_cause_and_confidence_are_consistent_with_the_rca_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_incident_reporter_evaluation::test_timeline_timestamps_are_grounded_in_the_upstream_reports` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.test_incident_reporter_agent::test_agent_backstory_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_does_not_delegate` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_agent_role_goal_backstory_match_spec` | PASS |  |
| `tests.test_incident_reporter_agent::test_build_agent_without_llm_requires_google_api_key` | PASS |  |
| `tests.test_incident_reporter_agent::test_default_incident_metadata_matches_the_real_incident_record` | PASS |  |
| `tests.test_incident_reporter_agent::test_remediation_recommendations_reuse_the_exact_recommendation_schema` | PASS |  |
| `tests.test_incident_reporter_agent::test_report_schema_has_exactly_the_fourteen_requested_fields` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_all_six_upstream_reports_verbatim` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_embeds_incident_metadata` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_altering_remediation_recommendations` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_description_forbids_inventing_evidence` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_expected_output_names_every_required_field` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_has_no_tools` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_is_assigned_to_the_given_agent` | PASS |  |
| `tests.test_incident_reporter_agent::test_task_output_pydantic_is_set` | PASS |  |
| `tests.test_incident_reporter_agent::test_timeline_entry_schema_supports_source_attribution` | PASS |  |

## Cross-cutting: LLM-as-judge rubric evaluations

Per docs/evaluation.md §5, these supplement (never replace) the structural checks above and require a live `GOOGLE_API_KEY`; they are SKIP, not FAIL, when no key is configured in this environment.

46 total -- 0 passed, 46 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_identifies_at_least_one_observed_fact` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_identifies_database_pressure_as_abnormal` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_never_reports_a_known_unavailable_metric` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_observed_facts_match_tool_ground_truth_exactly` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_provides_at_least_one_possible_cause` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_provides_interpretation_distinct_from_facts` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_reports_confidence_in_valid_range` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloud_infrastructure_analyst_evaluation::test_agent_summary_is_non_empty` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_all_seven_tasks_completed` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_each_task_produced_the_expected_structured_output_type` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_final_incident_report_has_remediation_requiring_human_approval` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_final_incident_report_identifies_the_golden_scenario_incident` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_final_output_is_the_incident_report` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_cloudops_investigation_crew_evaluation::test_no_tool_failures_across_the_whole_investigation` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_flow_evaluation::test_flow_produces_a_complete_incident_report` | **FAIL** | assert None is not None |
| `tests.evaluation.test_flow_evaluation::test_flow_result_requires_human_approval` | **FAIL** | TypeError: 'NoneType' object is not subscriptable |
| `tests.evaluation.test_flow_evaluation::test_flow_succeeds_end_to_end` | **FAIL** | AssertionError: assert 'failed' == 'succeeded' |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_cites_source_for_every_retrieved_chunk` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_distinguishes_knowledge_from_incident_evidence` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_every_procedure_has_a_safety_note` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_identifies_troubleshooting_procedures` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_never_fabricates_retrieved_text` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_production_safety_note_reflects_read_only_system` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_reports_confidence_in_valid_range` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_retrieved_sources_match_tool_ground_truth` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_retrieves_at_least_one_knowledge_chunk` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_knowledge_rag_evaluation::test_agent_summary_is_non_empty` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_cited_events_match_tool_ground_truth_verbatim` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_cites_relevant_events` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_does_not_default_to_root_cause_without_justification` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_identifies_pod_restart_patterns` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_identifies_probe_failures` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_makes_a_deployment_health_determination` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_makes_an_explicit_root_cause_assessment` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_pod_restart_counts_match_tool_ground_truth` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_reports_confidence_in_valid_range` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_kubernetes_reliability_analyst_evaluation::test_agent_summary_is_non_empty` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_error_findings_match_tool_ground_truth_exactly` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_extracts_timestamps` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_finds_at_least_one_error` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_finds_at_least_one_warning` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_identifies_recurring_patterns` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_never_invents_evidence` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_reports_confidence_in_valid_range` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_summary_is_non_empty` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |
| `tests.evaluation.test_log_analyst_evaluation::test_agent_warning_findings_match_tool_ground_truth_exactly` | **FAIL** | failed on setup with "google.genai.errors.ClientError: 429 RESOURCE_EXHAUSTED. {'error': {'code': 42 |

## Foundational / infrastructure tests

Support multiple categories above (simulated incident data, LLM client config) rather than mapping to exactly one.

36 total -- 36 passed, 0 failed, 0 skipped

| Test | Status | Detail |
|---|---|---|
| `tests.test_incident_data::test_incident_evidence_source_paths_exist` | PASS |  |
| `tests.test_incident_data::test_incident_json_has_required_fields` | PASS |  |
| `tests.test_incident_data::test_incident_matches_spec` | PASS |  |
| `tests.test_incident_data::test_incident_time_window_is_ordered` | PASS |  |
| `tests.test_incident_data::test_kubernetes_each_restarted_pod_has_a_killing_event` | PASS |  |
| `tests.test_incident_data::test_kubernetes_events_contain_liveness_failures` | PASS |  |
| `tests.test_incident_data::test_kubernetes_json_has_required_structure` | PASS |  |
| `tests.test_incident_data::test_kubernetes_no_deploy_during_incident_window` | PASS |  |
| `tests.test_incident_data::test_kubernetes_pod_count_matches_desired_replicas` | PASS |  |
| `tests.test_incident_data::test_kubernetes_restart_total_matches_metrics_peak` | PASS |  |
| `tests.test_incident_data::test_log_file_contains_database_pressure_evidence` | PASS |  |
| `tests.test_incident_data::test_log_file_is_not_json_or_markdown` | PASS |  |
| `tests.test_incident_data::test_log_file_pod_names_match_kubernetes_pods` | PASS |  |
| `tests.test_incident_data::test_log_file_shows_pod_restart_boot_sequence` | PASS |  |
| `tests.test_incident_data::test_log_file_timestamps_within_incident_window` | PASS |  |
| `tests.test_incident_data::test_metrics_datapoints_are_chronologically_sorted` | PASS |  |
| `tests.test_incident_data::test_metrics_datapoints_are_internally_consistent` | PASS |  |
| `tests.test_incident_data::test_metrics_db_cpu_exceeds_pod_cpu_at_peak` | PASS |  |
| `tests.test_incident_data::test_metrics_db_cpu_present_and_peaks_near_92_pct` | PASS |  |
| `tests.test_incident_data::test_metrics_http_5xx_rate_peaks_near_8_7_pct` | PASS |  |
| `tests.test_incident_data::test_metrics_json_has_required_structure` | PASS |  |
| `tests.test_incident_data::test_metrics_latency_peaks_near_four_seconds` | PASS |  |
| `tests.test_incident_data::test_metrics_recovers_toward_baseline_by_end_of_window` | PASS |  |
| `tests.test_incident_data::test_metrics_show_database_pressure_evidence` | PASS |  |
| `tests.test_incident_data::test_runbook_is_markdown_with_expected_sections` | PASS |  |
| `tests.test_incident_data::test_runbook_references_the_incident` | PASS |  |
| `tests.test_llm_config::test_get_google_api_key_reads_from_environment` | PASS |  |
| `tests.test_llm_config::test_is_configured_false_when_key_blank` | PASS |  |
| `tests.test_llm_config::test_is_configured_false_when_key_missing` | PASS |  |
| `tests.test_llm_config::test_is_configured_true_when_key_present` | PASS |  |
| `tests.test_llm_config::test_missing_api_key_raises_missing_api_key_error` | PASS |  |
| `tests.test_llm_service::test_check_connectivity_fails_gracefully_when_api_key_missing` | PASS |  |
| `tests.test_llm_service::test_check_connectivity_never_leaks_api_key_on_failure` | PASS |  |
| `tests.test_llm_service::test_check_connectivity_succeeds_when_llm_responds` | PASS |  |
| `tests.test_llm_service::test_get_llm_builds_llm_with_configured_model_and_key` | PASS |  |
| `tests.test_llm_service::test_get_llm_raises_when_api_key_missing` | PASS |  |

## Adversarial / failure scenarios (required by Phase 21)

Ten scenarios, each with at least one dedicated test in `tests/evaluation_suite/test_failure_scenarios.py`. Every scenario below must show at least one PASS row with no FAIL rows for that scenario to be considered covered.

### Missing log file -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_missing_log_file_fails_cleanly_not_silently` | PASS |  |
| `tests.test_log_parser::test_missing_log_file_raises_file_not_found` | PASS |  |

### Malformed metrics -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_malformed_metrics_json_fails_cleanly_not_silently` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_metrics_missing_required_fields_reports_unavailable_not_invented` | PASS |  |

### Missing Kubernetes data -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_malformed_kubernetes_json_fails_cleanly_not_silently` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_missing_kubernetes_file_fails_cleanly_not_silently` | PASS |  |
| `tests.test_kubernetes_parser::test_missing_kubernetes_file_raises_file_not_found` | PASS |  |

### RAG unavailable -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_knowledge_tool_with_empty_runbooks_dir_returns_empty_not_fabricated` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_knowledge_tool_with_unavailable_runbooks_dir_fails_cleanly` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_rag_unavailable_missing_runbooks_directory_fails_cleanly` | PASS |  |

### LLM timeout -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_api_handles_an_llm_timeout_gracefully` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_flow_handles_an_llm_timeout_gracefully` | PASS |  |

### Invalid incident -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_api_returns_404_for_an_invalid_incident` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_invalid_incident_id_is_rejected_before_any_agent_runs` | PASS |  |

### Incomplete evidence -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_incomplete_upstream_reports_do_not_crash_task_construction` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_rubric_flags_missing_evidence_when_evidence_is_sparse` | PASS |  |

### Prompt injection in logs -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_log_tool_treats_injected_instructions_as_inert_data` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_schema_rejects_an_approval_bypass_even_if_something_tried_to_inject_one` | PASS |  |

### Prompt injection in runbooks -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_rag_treats_injected_runbook_instructions_as_inert_data` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_schema_still_rejects_bypass_from_a_runbook_injection` | PASS |  |

### Hallucination attempts -- PASS

| Test | Status | Detail |
|---|---|---|
| `tests.evaluation_suite.test_failure_scenarios::test_knowledge_tool_rejects_an_unrelated_query_instead_of_fabricating_a_match` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_knowledge_tool_still_returns_genuinely_relevant_matches` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_metrics_tool_never_reports_a_metric_absent_from_the_source_file` | PASS |  |
| `tests.evaluation_suite.test_failure_scenarios::test_rubric_catches_a_fabricated_metric_in_a_root_cause_report` | PASS |  |

