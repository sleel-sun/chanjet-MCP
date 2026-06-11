# MCP Client Flexible Calls Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add safe configuration diagnostics, official-doc call templates, and predictable tool error envelopes for MCP clients.

**Architecture:** Keep MCP wrappers thin in `server.py`. Add product normalization, diagnostics, template extraction, and error envelope helpers to `ChanjetTCloudClient` so tests can run with fake transports and token stores. Preserve existing raw API call tools for compatibility.

**Tech Stack:** Python 3.10+, `unittest`, existing `FastMCP`, existing `JsonTransport`, existing `TokenStore`.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py` to add diagnostics, product metadata normalization, API template extraction, and error envelope helpers.
- Modify `src/chanjet_tcloud_mcp/server.py` to expose `diagnose_config` and `get_api_call_template` MCP tools.
- Modify `README.md` to document the new tools and intended client flow.
- Modify `tests/test_client.py` to cover the new client behavior with fake transports and temporary token stores.

## Task 1: Configuration Diagnostics

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing diagnostics tests**

Add tests for a missing-credential setup and a stored active account setup. Assert that diagnostics never include token values, report issues with machine-readable codes, and set capability booleans correctly.

- [ ] **Step 2: Run diagnostics tests**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_diagnose_config_reports_missing_credentials tests.test_client.ClientTests.test_diagnose_config_reports_active_stored_account -v`

Expected: fail because `diagnose_config` does not exist.

- [ ] **Step 3: Implement minimal diagnostics**

Add `ChanjetTCloudClient.diagnose_config()` that inspects settings and token store only. Include `settings`, `accounts`, `capabilities`, and `issues`.

- [ ] **Step 4: Run diagnostics tests again**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_diagnose_config_reports_missing_credentials tests.test_client.ClientTests.test_diagnose_config_reports_active_stored_account -v`

Expected: pass.

## Task 2: API Call Templates

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing template tests**

Add tests that call `get_api_call_template(product="tplus", parent_code="t+jcda", module_code="t+ck")` against a representative official doc payload. Assert product alias normalization, recommended tool name, extracted path, method, body placeholder, and ready-to-edit arguments.

- [ ] **Step 2: Run template tests**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_get_api_call_template_extracts_tplus_templates tests.test_client.ClientTests.test_get_api_call_template_filters_by_api_name -v`

Expected: fail because `get_api_call_template` does not exist.

- [ ] **Step 3: Implement template extraction**

Add product metadata for `tcloud/tplus`, `hyc/zplus`, `hsy/haoshengyi`, `ydz/finance`, and `hkj/accounting`. Fetch docs through existing `get_doc`, scan dict/list values defensively for API entries, and build template objects with conservative defaults.

- [ ] **Step 4: Run template tests again**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_get_api_call_template_extracts_tplus_templates tests.test_client.ClientTests.test_get_api_call_template_filters_by_api_name -v`

Expected: pass.

## Task 3: Error Envelopes and MCP Wrappers

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Modify: `src/chanjet_tcloud_mcp/server.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing envelope tests**

Add tests for `tool_success`, `tool_error`, and invalid product handling through a safe template wrapper method. Assert `{ok: true, data: ...}` and `{ok: false, error: {code, message, hint, trace_id}}`.

- [ ] **Step 2: Run envelope tests**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_tool_error_envelope_from_value_error tests.test_client.ClientTests.test_safe_get_api_call_template_wraps_invalid_product -v`

Expected: fail because the helpers do not exist.

- [ ] **Step 3: Implement envelopes and server tools**

Add `tool_success`, `tool_error`, and `safe_get_api_call_template` to the client. Add `diagnose_config` and `get_api_call_template` MCP tools to `server.py`; both return normalized wrapper objects.

- [ ] **Step 4: Run envelope tests again**

Run: `PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_tool_error_envelope_from_value_error tests.test_client.ClientTests.test_safe_get_api_call_template_wraps_invalid_product -v`

Expected: pass.

## Task 4: Documentation and Full Verification

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Document new client flow**

Add README entries for `diagnose_config` and `get_api_call_template`, including sample responses and the recommended flow: diagnose, search docs, generate template, call product tool.

- [ ] **Step 2: Run full test suite**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`

Expected: all tests pass.

- [ ] **Step 3: Check import of MCP server**

Run: `.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"`

Expected: prints `chanjet-tcloud`.

## Task 5: Simplified Client Template Search and Calls

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Modify: `src/chanjet_tcloud_mcp/server.py`
- Modify: `README.md`
- Test: `tests/test_client.py`

- [ ] **Step 1: Write failing tests for simplified template search**

Add `test_search_api_templates_returns_ready_to_call_templates` to verify that a keyword and optional product can return enriched templates with product metadata, module metadata, recommended tool, and ready-to-edit arguments.

- [ ] **Step 2: Write failing tests for template-driven calls**

Add `test_call_api_template_routes_to_matching_product_call` to verify that product/module/API name plus request body loads the official template and routes through the correct low-level product call.

- [ ] **Step 3: Implement client methods**

Add `search_api_templates`, `call_api_template`, `safe_search_api_templates`, `safe_call_api_template`, and product routing helper logic to `ChanjetTCloudClient`.

- [ ] **Step 4: Expose MCP tools**

Add `search_api_templates` and `call_api_template` wrappers to `server.py`, returning the existing `{ok, data/error}` envelope.

- [ ] **Step 5: Verify**

Run: `PYTHONPATH=src python3 -m unittest discover -s tests -v`

Expected: all tests pass.
