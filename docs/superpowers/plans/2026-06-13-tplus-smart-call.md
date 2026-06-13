# T+ Smart API Call Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a high-level T+ API call helper that starts from the official request example and resolves common natural-language codes and fields before calling T+.

**Architecture:** Keep existing low-level tools unchanged. Add `ChanjetTCloudClient.call_tplus_api_smart` that composes existing template, reference-code, voucher-field, and T+ call helpers, plus a safe wrapper and thin MCP server function.

**Tech Stack:** Python 3.10+, `unittest`, existing fake transport tests, existing `FastMCP` wrapper.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py` to add smart-call orchestration and helper methods for deep merge, reference resolution, and filter/display matching.
- Modify `src/chanjet_tcloud_mcp/server.py` to expose `call_tplus_api_smart`.
- Modify `tests/test_client.py` to cover template-first request construction, natural-language resolution, and unresolved-field errors.
- Modify `README.md` to document usage.

## Task 1: Failing Tests

- [x] **Step 1: Add smart-call tests**

Add tests for:

- Official template is fetched first and used as the base request.
- `voucher_name`, `business_type_name`, natural-language filters, and display fields resolve before calling.
- Unmatched filter fields raise `ValueError` and do not call the business API.
- Safe wrapper returns `{ok: false, error: ...}` for unresolved inputs.

- [x] **Step 2: Verify tests fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_call_tplus_api_smart_uses_template_and_resolves_natural_inputs tests.test_client.ClientTests.test_call_tplus_api_smart_rejects_unmatched_filter tests.test_client.ClientTests.test_safe_call_tplus_api_smart_wraps_unmatched_filter -v
```

Expected: fail because `call_tplus_api_smart` does not exist.

## Task 2: Client Implementation

- [x] **Step 1: Implement minimal smart-call orchestration**

Implement `call_tplus_api_smart` by fetching `get_api_call_template(product="tplus", ...)`, copying template arguments, resolving codes/fields, deep-merging overrides, and calling `call_tplus_api`.

- [x] **Step 2: Implement safe wrapper**

Add `safe_call_tplus_api_smart`.

- [x] **Step 3: Verify targeted tests pass**

Run the command from Task 1 Step 2.

Expected: tests pass.

## Task 3: MCP Wrapper and Docs

- [x] **Step 1: Add server wrapper**

Expose `call_tplus_api_smart` in `server.py` with a docstring that tells clients this tool references the official request example before calling.

- [x] **Step 2: Update README**

Document the required docs identifiers and natural-language fields.

- [x] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
git diff --check
```

Expected: all tests pass, import prints `chanjet-tcloud`, and diff check prints nothing.
