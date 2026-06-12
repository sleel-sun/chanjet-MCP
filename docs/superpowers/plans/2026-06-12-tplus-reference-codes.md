# T+ Reference Codes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a safe MCP lookup tool for T+ document type `bizCode` and business type `BusinessType` reference tables.

**Architecture:** Keep `server.py` as a thin wrapper and implement fetching, extraction, filtering, and envelopes in `ChanjetTCloudClient`. Reuse the existing official document API path builder and safe envelope helpers.

**Tech Stack:** Python 3.10+, `unittest`, existing `FastMCP`, existing fake transport test pattern.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py` to add constants, `get_tplus_reference_codes`, `safe_get_tplus_reference_codes`, and private extraction/filter helpers.
- Modify `src/chanjet_tcloud_mcp/server.py` to expose the `get_tplus_reference_codes` MCP tool.
- Modify `tests/test_client.py` to cover fetching both official docs, normalization, query filtering, and safe error envelopes.
- Modify `README.md` to document the new tool and advise using it before unknown `bizCode` or `BusinessType` calls.

## Task 1: Client Behavior

- [ ] **Step 1: Write failing tests**

Add tests in `tests/test_client.py`:

```python
def test_get_tplus_reference_codes_fetches_voucher_and_business_type_docs(self):
    client, transport = self.make_client([
        {"result": True, "error": None, "value": {"rows": [{"code": "SA04", "name": "销货单"}]}},
        {"result": True, "error": None, "value": {"rows": [{"code": "02", "name": "采购退货"}]}},
    ])

    result = client.get_tplus_reference_codes()

    self.assertEqual(result["voucher_types"][0]["code"], "SA04")
    self.assertEqual(result["voucher_types"][0]["name"], "销货单")
    self.assertEqual(result["business_types"][0]["code"], "02")
    self.assertEqual(result["business_types"][0]["name"], "采购退货")
    self.assertEqual(
        [call["url"] for call in transport.calls],
        [
            "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bxdescription/t%2Bvouchertype",
            "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bxdescription/t%2Bbusitype",
        ],
    )
```

```python
def test_get_tplus_reference_codes_filters_by_query(self):
    client, _transport = self.make_client([
        {"result": True, "error": None, "value": {"rows": [{"code": "SA04", "name": "销货单"}, {"code": "PU01", "name": "采购订单"}]}},
        {"result": True, "error": None, "value": {"rows": [{"code": "01", "name": "普通采购"}, {"code": "02", "name": "采购退货"}]}},
    ])

    result = client.get_tplus_reference_codes(query="采购退货")

    self.assertEqual(result["voucher_types"], [])
    self.assertEqual(result["business_types"][0]["code"], "02")
```

- [ ] **Step 2: Verify failing tests**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_get_tplus_reference_codes_fetches_voucher_and_business_type_docs tests.test_client.ClientTests.test_get_tplus_reference_codes_filters_by_query -v
```

Expected: fail because `get_tplus_reference_codes` does not exist.

- [ ] **Step 3: Implement minimal client code**

Add `TPLUS_DESCRIPTION_PARENT_CODE`, `TPLUS_VOUCHER_TYPE_MODULE_CODE`, and `TPLUS_BUSINESS_TYPE_MODULE_CODE`; fetch both docs through `get_tcloud_doc`; recursively collect dict/list rows; normalize code/name keys; filter by optional query.

- [ ] **Step 4: Verify client tests pass**

Run the same command from Step 2.

Expected: both tests pass.

## Task 2: Server Tool and Docs

- [ ] **Step 1: Add safe wrapper test**

Add a test that `safe_get_tplus_reference_codes(query="SA04")` returns `{ok: True, data: ...}`.

- [ ] **Step 2: Implement wrapper and MCP tool**

Add `safe_get_tplus_reference_codes` to `client.py` and `get_tplus_reference_codes` to `server.py`.

- [ ] **Step 3: Update README**

Document `get_tplus_reference_codes` and update the `query_tplus_voucher_list` section to instruct clients to call it when `biz_code` or `BusinessType` is unknown.

- [ ] **Step 4: Full verification**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
```

Expected: all tests pass and import prints `chanjet-tcloud`.
