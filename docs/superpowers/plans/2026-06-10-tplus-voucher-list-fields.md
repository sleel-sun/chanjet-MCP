# T+ Voucher List Display Fields Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a dedicated MCP tool that preloads T+ voucher list display columns and maps requested display fields before querying voucher list data.

**Architecture:** Keep the generic `call_tplus_api` unchanged. Add a specialized `ChanjetTCloudClient.query_tplus_voucher_list` method that composes the official column helper call and the caller-provided list query call, then expose it through a thin `server.py` MCP wrapper.

**Tech Stack:** Python 3.10+, `unittest`, existing MCP `FastMCP` wrapper, existing `JsonTransport` abstraction.

---

### Task 1: Client Behavior Tests

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Write failing tests**

Add tests that call `client.query_tplus_voucher_list(...)`, assert the first request targets `/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`, assert requested display fields are matched, and assert the list query body receives `param.selectFields`.

- [ ] **Step 2: Verify tests fail**

Run: `.venv/bin/python -m unittest tests.test_client.ClientTests.test_query_tplus_voucher_list_fetches_and_matches_display_fields`

Expected: fail with `AttributeError` because `query_tplus_voucher_list` is not implemented.

### Task 2: Client Implementation

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`

- [ ] **Step 1: Implement minimal client method and helpers**

Add `query_tplus_voucher_list`, `_voucher_column_request_body`, `_extract_voucher_display_fields`, `_normalize_display_field`, `_match_display_fields`, `_inject_display_fields`, and small normalization helpers.

- [ ] **Step 2: Verify client tests pass**

Run: `.venv/bin/python -m unittest tests.test_client`

Expected: all client tests pass.

### Task 3: MCP Wrapper And Docs

**Files:**
- Modify: `src/chanjet_tcloud_mcp/server.py`
- Modify: `README.md`

- [ ] **Step 1: Add MCP wrapper**

Add `query_tplus_voucher_list` in `server.py` with the same argument shape as the client method.

- [ ] **Step 2: Document usage**

Add a README section showing a `query_tplus_voucher_list` JSON example.

- [ ] **Step 3: Verify full test suite and syntax**

Run: `.venv/bin/python -m unittest`

Expected: all tests pass.

Run: `.venv/bin/python -m py_compile src/chanjet_tcloud_mcp/*.py`

Expected: command exits successfully.

## Self-Review

The plan covers the approved design, has no placeholder implementation steps, and keeps the enhancement isolated from generic API passthrough behavior.
