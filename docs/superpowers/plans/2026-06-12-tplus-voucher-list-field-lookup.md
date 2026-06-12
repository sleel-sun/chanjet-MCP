# T+ Voucher List Field Lookup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add an MCP tool that fetches T+ voucher list query fields and display columns using the helper APIs documented by `tcloud/t+dj/djlbcxfz`.

**Architecture:** Keep generic `call_tplus_api` unchanged. Add a client lookup method that calls `GetSearchItemByBizCode` and `GetColumnSetByBizCode`, normalizes both responses with the existing field normalization logic, and expose it through a safe MCP wrapper. Update `query_tplus_voucher_list` to use the same lookup path and include `query_fields` in its response.

**Tech Stack:** Python 3.10+, `unittest`, existing fake transport tests, existing `FastMCP` wrapper.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py` for constants, lookup method, safe wrapper, filtering helper, and `query_tplus_voucher_list` integration.
- Modify `src/chanjet_tcloud_mcp/server.py` to expose `get_tplus_voucher_list_fields` and improve related tool descriptions.
- Modify `tests/test_client.py` for TDD coverage of the new lookup tool and updated list-query behavior.
- Modify `README.md` to document query fields, display columns, and the new tool.

## Task 1: Lookup Tests

- [ ] **Step 1: Write failing tests**

Add tests for `get_tplus_voucher_list_fields` that assert:

- It calls `/tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode`.
- It calls `/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`.
- It returns normalized `query_fields`, `display_fields`, and `source_doc`.
- `query` filters both lists.

- [ ] **Step 2: Verify tests fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_get_tplus_voucher_list_fields_fetches_query_and_display_fields tests.test_client.ClientTests.test_get_tplus_voucher_list_fields_filters_by_query -v
```

Expected: fail because `get_tplus_voucher_list_fields` does not exist.

## Task 2: Client Implementation

- [ ] **Step 1: Add minimal implementation**

Add `TPLUS_VOUCHER_SEARCH_ITEM_PATH`, `TPLUS_VOUCHER_LIST_FIELD_DOC_PARENT_CODE`, and `TPLUS_VOUCHER_LIST_FIELD_DOC_MODULE_CODE`. Implement `get_tplus_voucher_list_fields`, `safe_get_tplus_voucher_list_fields`, and `_filter_voucher_fields`.

- [ ] **Step 2: Verify lookup tests pass**

Run the command from Task 1 Step 2.

Expected: both lookup tests pass.

## Task 3: Integrate List Query Tool

- [ ] **Step 1: Update existing tests**

Update `query_tplus_voucher_list` tests so the helper call sequence is search items, display columns, then list query. Assert the response includes `query_fields`.

- [ ] **Step 2: Update implementation**

Change `query_tplus_voucher_list` to call `get_tplus_voucher_list_fields` before the list API call, use returned `display_fields` for matching, and include returned `query_fields` in the response.

- [ ] **Step 3: Verify tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_query_tplus_voucher_list_fetches_and_matches_display_fields tests.test_client.ClientTests.test_query_tplus_voucher_list_preserves_existing_field_selection -v
```

Expected: both tests pass.

## Task 4: MCP Wrapper and Documentation

- [ ] **Step 1: Add server wrapper**

Expose `get_tplus_voucher_list_fields` in `server.py` with a docstring instructing clients to call it when query fields or display columns are unknown.

- [ ] **Step 2: Update README**

Document the new tool and update `query_tplus_voucher_list` usage guidance.

- [ ] **Step 3: Full verification**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
git diff --check
```

Expected: all tests pass, import prints `chanjet-tcloud`, and diff check prints nothing.
