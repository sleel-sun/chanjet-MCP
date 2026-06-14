# T+ Smart Voucher List Query Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `query_tplus_voucher_list_smart`, a high-level T+ list-query tool that resolves natural voucher names, finds official list templates, builds `pageSize/pageIndex/paramDic/selectFields`, and calls the business API without per-voucher path hardcoding.

**Architecture:** Keep `server.py` thin and implement orchestration in `ChanjetTCloudClient`. Reuse existing official document/template search, T+ `bizCode` reference parsing, voucher list field lookup, field matching, deep merge, and authenticated `call_tplus_api`. Add only small fallback maps for missing stable `bizCode` values and known bad module-code aliases.

**Tech Stack:** Python 3.10+, standard-library `unittest`, existing fake `JsonTransport`, MCP `FastMCP`.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py`: add constants, smart voucher-list method, safe wrapper, and generic helper methods.
- Modify `src/chanjet_tcloud_mcp/server.py`: expose `query_tplus_voucher_list_smart` as a thin MCP wrapper.
- Modify `tests/test_client.py`: add failing client tests for success, compatibility, request generation, and no-template error.
- Modify `README.md`: document when to use `query_tplus_voucher_list_smart`.

## Task 1: Client Tests

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Add a failing success-path test**

Insert this test in `tests/test_client.py` after `test_call_tplus_api_smart_uses_template_and_resolves_natural_inputs`:

```python
    def test_query_tplus_voucher_list_smart_resolves_template_and_generates_body(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"rows": [{"code": "SA04", "name": "销货单"}]},
                },
                {"result": True, "error": None, "value": {"rows": []}},
                {
                    "result": True,
                    "error": None,
                    "value": {"productCode": "tcloud", "children": []},
                },
                {
                    "result": True,
                    "error": None,
                    "value": {"productCode": "tcloud", "children": []},
                },
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "tcloud",
                        "children": [
                            {
                                "moduleCode": "t+sc",
                                "moduleName": "生产管理",
                                "children": [
                                    {
                                        "moduleCode": "manufactureOrder",
                                        "moduleName": "生产加工单",
                                    }
                                ],
                            }
                        ],
                    },
                },
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "T+Cloud / 生产管理 / 生产加工单",
                        "moduleName": "生产加工单",
                        "documentApiInfoList": [
                            {
                                "apiName": "生产加工单列表查询",
                                "apiUrl": "/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
                                "requestMethod": "POST",
                                "requestBody": {"param": {}},
                            }
                        ],
                    },
                },
                {
                    "code": "0",
                    "data": {
                        "items": [
                            {"FieldName": "Code", "Caption": "单据编号"},
                            {"FieldName": "VoucherDate", "Caption": "单据日期"},
                        ]
                    },
                },
                {
                    "code": "0",
                    "data": {
                        "columns": [
                            {"FieldName": "Code", "Caption": "单据编号"},
                            {"FieldName": "Quantity", "Caption": "数量"},
                        ]
                    },
                },
                {"code": "0", "data": [{"Code": "MO-001", "Quantity": 3}]},
            ]
        )

        result = client.query_tplus_voucher_list_smart(
            voucher_name="生产加工单",
            intent="查询所有",
            module_code="ManufactureOrderOpenApi",
            filters={"单据编号": "MO-001"},
            display_fields=["单据编号", "数量"],
            page_size=50,
            page_index=2,
            body_overrides={"param": {"paramDic": {"extra": "x"}}},
        )

        self.assertEqual(result["resolved"]["biz_code"], "MP05")
        self.assertEqual(result["resolved"]["biz_code_source"], "fallback")
        self.assertEqual(result["template"]["api_name"], "生产加工单列表查询")
        self.assertEqual(
            result["request"]["path"],
            "/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
        )
        self.assertEqual(
            transport.calls[8]["json_body"],
            {
                "param": {
                    "pageSize": 50,
                    "pageIndex": 2,
                    "paramDic": {"Code": "MO-001", "extra": "x"},
                    "selectFields": ["Code", "Quantity"],
                }
            },
        )
        self.assertEqual(
            result["resolved"]["matched_filter_fields"],
            [{"requested": "单据编号", "field": "Code", "label": "单据编号"}],
        )
        self.assertEqual(
            result["resolved"]["matched_display_fields"],
            [
                {"requested": "单据编号", "field": "Code", "label": "单据编号"},
                {"requested": "数量", "field": "Quantity", "label": "数量"},
            ],
        )
        self.assertEqual(
            result["resolved"]["compatibility"],
            [
                {
                    "input": "ManufactureOrderOpenApi",
                    "decision": "ignored_module_code_alias",
                    "reason": "module_code looks like an API implementation alias, so voucher_name search was used",
                }
            ],
        )
        self.assertEqual(
            [call["url"] for call in transport.calls],
            [
                "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bxdescription/t%2Bvouchertype",
                "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bxdescription/t%2Bbusitype",
                "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/tcloud",
                "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/tcloud",
                "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/tcloud",
                "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bsc/manufactureOrder",
                "https://openapi.chanjet.com/tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode",
                "https://openapi.chanjet.com/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode",
                "https://openapi.chanjet.com/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
            ],
        )
        self.assertEqual(result["data"], {"code": "0", "data": [{"Code": "MO-001", "Quantity": 3}]})
```

- [ ] **Step 2: Run the success-path test to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_client.ClientTests.test_query_tplus_voucher_list_smart_resolves_template_and_generates_body
```

Expected: FAIL with `AttributeError: 'ChanjetTCloudClient' object has no attribute 'query_tplus_voucher_list_smart'`.

- [ ] **Step 3: Add a failing no-template safe-wrapper test**

Insert this test after the success-path test:

```python
    def test_safe_query_tplus_voucher_list_smart_wraps_missing_template(self):
        client, transport = self.make_client(
            [
                {"result": True, "error": None, "value": {"rows": []}},
                {"result": True, "error": None, "value": {"rows": []}},
                {
                    "result": True,
                    "error": None,
                    "value": {"productCode": "tcloud", "children": []},
                },
                {
                    "result": True,
                    "error": None,
                    "value": {"productCode": "tcloud", "children": []},
                },
                {
                    "result": True,
                    "error": None,
                    "value": {"productCode": "tcloud", "children": []},
                },
            ]
        )

        result = client.safe_query_tplus_voucher_list_smart(
            voucher_name="生产加工单",
            intent="列表",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_argument")
        self.assertIn("No T+ voucher list template matched", result["error"]["message"])
        self.assertIn("query_tplus_voucher_list_smart", result["error"]["hint"])
        self.assertEqual(len(transport.calls), 5)
```

- [ ] **Step 4: Run both new tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_client.ClientTests.test_query_tplus_voucher_list_smart_resolves_template_and_generates_body tests.test_client.ClientTests.test_safe_query_tplus_voucher_list_smart_wraps_missing_template
```

Expected: FAIL with missing `query_tplus_voucher_list_smart` and `safe_query_tplus_voucher_list_smart`.

- [ ] **Step 5: Commit tests**

Run:

```bash
git add tests/test_client.py
git commit -m "test: cover smart T+ voucher list query"
```

## Task 2: Client Implementation

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Add constants**

In `src/chanjet_tcloud_mcp/client.py`, add these constants after `TPLUS_BUSINESS_TYPE_MODULE_CODE`:

```python
TPLUS_LIST_INTENT_MARKERS = ("列表", "查询", "所有", "全部", "list", "query", "all")
TPLUS_LIST_TEMPLATE_MARKERS = ("findvoucherlist", "列表查询", "列表", "查询")
TPLUS_VOUCHER_BIZ_CODE_FALLBACKS = {
    "生产加工单": "MP05",
}
TPLUS_MODULE_CODE_ALIASES = {
    "manufactureorderopenapi": "module_code looks like an API implementation alias, so voucher_name search was used",
}
```

- [ ] **Step 2: Add public client methods**

Add these methods after `query_tplus_voucher_list`:

```python
    def query_tplus_voucher_list_smart(
        self,
        *,
        voucher_name: str,
        intent: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        page_size: int = 20,
        page_index: int = 1,
        body_overrides: Any = None,
        parent_code: str | None = None,
        module_code: str | None = None,
        api_name: str | None = None,
        path: str | None = None,
        method: str | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        if not voucher_name or not str(voucher_name).strip():
            raise ValueError("voucher_name is required")
        if not self._is_tplus_list_intent(intent):
            raise ValueError(
                "Unsupported T+ voucher list intent; use call_api_smart for non-list operations"
            )

        resolved_code = self._resolve_tplus_voucher_biz_code(voucher_name)
        template_result = self._find_tplus_voucher_list_template(
            voucher_name=voucher_name,
            intent=intent,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
            path=path,
            method=method,
        )
        template = template_result["template"]

        field_data = self.get_tplus_voucher_list_fields(
            biz_code=resolved_code["biz_code"],
            headers=headers,
            account_alias=account_alias,
        )
        request_body = self._tplus_list_body(
            template.get("body"),
            page_size=page_size,
            page_index=page_index,
        )
        matched_filter_fields = self._inject_tplus_list_filters(
            request_body,
            filters or {},
            field_data["query_fields"],
        )
        matched_display_fields, unmatched_display_fields = self._match_display_fields(
            display_fields or [],
            field_data["display_fields"],
        )
        if unmatched_display_fields:
            raise ValueError(
                f"Unmatched display fields: {', '.join(unmatched_display_fields)}"
            )
        request_body = self._inject_display_fields(
            request_body,
            [field["field"] for field in matched_display_fields],
        )
        if body_overrides is not None:
            request_body = self._deep_merge_values(request_body, body_overrides)

        request_args = {
            "path": template_result["path"],
            "method": method or template.get("method") or "POST",
            "body": request_body,
            "query": query or {},
            "headers": headers or {},
            "account_alias": account_alias,
        }
        response = self.call_tplus_api(
            path=request_args["path"],
            method=request_args["method"],
            body=request_args["body"],
            query=request_args["query"],
            headers=request_args["headers"],
            account_alias=account_alias,
        )

        return {
            "data": response,
            "template": template,
            "request": request_args,
            "resolved": {
                "voucher_name": str(voucher_name).strip(),
                "intent": intent or "列表查询",
                "biz_code": resolved_code["biz_code"],
                "biz_code_source": resolved_code["source"],
                "module": template_result["module"],
                "selected_template_reason": template_result["reason"],
                "search_queries": template_result["search_queries"],
                "compatibility": template_result["compatibility"],
                "matched_filter_fields": matched_filter_fields,
                "matched_display_fields": matched_display_fields,
                "field_source_doc": field_data["source_doc"],
            },
        }

    def safe_query_tplus_voucher_list_smart(
        self,
        *,
        voucher_name: str,
        intent: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        page_size: int = 20,
        page_index: int = 1,
        body_overrides: Any = None,
        parent_code: str | None = None,
        module_code: str | None = None,
        api_name: str | None = None,
        path: str | None = None,
        method: str | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.query_tplus_voucher_list_smart(
                    voucher_name=voucher_name,
                    intent=intent,
                    filters=filters,
                    display_fields=display_fields,
                    page_size=page_size,
                    page_index=page_index,
                    body_overrides=body_overrides,
                    parent_code=parent_code,
                    module_code=module_code,
                    api_name=api_name,
                    path=path,
                    method=method,
                    query=query,
                    headers=headers,
                    account_alias=account_alias,
                )
            )
        except Exception as exc:
            return self.tool_error(
                exc,
                hint=(
                    "Use query_tplus_voucher_list_smart with voucher_name for natural list requests, "
                    "or call search_api_templates/get_api_call_template to inspect official modules."
                ),
            )
```

- [ ] **Step 3: Add generic helper methods**

Add these methods near existing T+ helper methods, before `_voucher_field_request_body`:

```python
    def _is_tplus_list_intent(self, intent: str | None) -> bool:
        if intent is None or not str(intent).strip():
            return True
        normalized = self._normalize_match_value(intent)
        raw = str(intent).casefold()
        return any(
            marker in raw or self._normalize_match_value(marker) in normalized
            for marker in TPLUS_LIST_INTENT_MARKERS
        )

    def _tplus_voucher_search_queries(
        self,
        voucher_name: str,
        intent: str | None,
    ) -> list[str]:
        base = str(voucher_name).strip()
        intent_text = str(intent).strip() if intent else "列表查询"
        candidates = [
            f"{base} {intent_text}",
            f"{base} 列表查询",
            f"{base} 查询",
            base,
        ]
        queries: list[str] = []
        for candidate in candidates:
            if candidate and candidate not in queries:
                queries.append(candidate)
        return queries

    def _resolve_tplus_voucher_biz_code(self, voucher_name: str) -> dict[str, str]:
        reference_lookup = self.get_tplus_reference_codes(query=voucher_name)
        try:
            return {
                "biz_code": self._resolve_reference_code(
                    reference_lookup["voucher_types"],
                    voucher_name,
                    label="voucher type",
                ),
                "source": "official",
            }
        except ValueError:
            normalized_name = self._normalize_match_value(voucher_name)
            for name, code in TPLUS_VOUCHER_BIZ_CODE_FALLBACKS.items():
                if self._normalize_match_value(name) == normalized_name:
                    return {"biz_code": code, "source": "fallback"}
        raise ValueError(f"Could not resolve voucher bizCode: {voucher_name}")

    def _find_tplus_voucher_list_template(
        self,
        *,
        voucher_name: str,
        intent: str | None,
        parent_code: str | None,
        module_code: str | None,
        api_name: str | None,
        path: str | None,
        method: str | None,
    ) -> dict[str, Any]:
        compatibility: list[dict[str, str]] = []
        normalized_module_code = self._normalize_tplus_module_hint(
            module_code,
            compatibility,
        )
        explicit_path = self._normalize_api_path(path) if path else None
        candidates: list[dict[str, Any]] = []
        search_queries: list[str] = []

        if parent_code and normalized_module_code:
            try:
                template_result = self.get_api_call_template(
                    product=TCLOUD_PRODUCT_CODE,
                    parent_code=parent_code,
                    module_code=normalized_module_code,
                    api_name=api_name,
                )
                for template in template_result["templates"]:
                    candidates.append(
                        {
                            "template": template,
                            "module": template_result["module"],
                            "path": explicit_path or template["path"],
                            "reason": "explicit_module",
                        }
                    )
            except Exception as exc:
                compatibility.append(
                    {
                        "input": str(module_code),
                        "decision": "ignored_unresolved_module_code",
                        "reason": str(exc),
                    }
                )

        for search_query in self._tplus_voucher_search_queries(voucher_name, intent):
            search_queries.append(search_query)
            result = self.search_api_templates(
                query=search_query,
                product=TCLOUD_PRODUCT_CODE,
                api_name=api_name,
                limit=10,
            )
            for template in result["templates"]:
                candidates.append(
                    {
                        "template": template,
                        "module": template.get("module", {}),
                        "path": explicit_path or template["path"],
                        "reason": "official_doc_search",
                    }
                )
            if candidates:
                break

        if explicit_path and not candidates:
            template = {
                "api_name": api_name or explicit_path,
                "path": explicit_path,
                "method": (method or "POST").upper(),
                "body": {},
                "query": {},
                "headers": {},
                "tool": "call_tplus_api",
                "arguments": {
                    "path": explicit_path,
                    "method": (method or "POST").upper(),
                    "body": {},
                    "query": {},
                    "headers": {},
                    "account_alias": None,
                },
                "raw": {},
            }
            return {
                "template": template,
                "module": {},
                "path": explicit_path,
                "reason": "explicit_path",
                "search_queries": search_queries,
                "compatibility": compatibility,
            }

        ranked_candidates = [
            (self._rank_tplus_voucher_list_template(candidate, voucher_name), candidate)
            for candidate in candidates
        ]
        ranked_candidates = [
            item for item in ranked_candidates if item[0][0] < 10
        ]
        if not ranked_candidates:
            raise ValueError(
                f"No T+ voucher list template matched voucher_name={voucher_name}"
            )

        _rank, selected = sorted(ranked_candidates, key=lambda item: item[0])[0]
        return {
            "template": selected["template"],
            "module": selected["module"],
            "path": selected["path"],
            "reason": selected["reason"],
            "search_queries": search_queries,
            "compatibility": compatibility,
        }

    def _rank_tplus_voucher_list_template(
        self,
        candidate: dict[str, Any],
        voucher_name: str,
    ) -> tuple[int, int]:
        template = candidate["template"]
        haystack = self._normalize_match_value(
            " ".join(
                str(value)
                for value in (
                    template.get("api_name"),
                    template.get("path"),
                    candidate.get("module", {}).get("module_name"),
                    candidate.get("module", {}).get("module_path"),
                )
                if value
            )
        )
        voucher_match = 0 if self._normalize_match_value(voucher_name) in haystack else 1
        if "findvoucherlist" in haystack:
            return (0, voucher_match)
        if any(
            self._normalize_match_value(marker) in haystack
            for marker in TPLUS_LIST_TEMPLATE_MARKERS
        ):
            return (1, voucher_match)
        return (10, voucher_match)

    def _normalize_tplus_module_hint(
        self,
        module_code: str | None,
        compatibility: list[dict[str, str]],
    ) -> str | None:
        if not module_code or not str(module_code).strip():
            return None
        normalized = self._normalize_match_value(module_code)
        reason = TPLUS_MODULE_CODE_ALIASES.get(normalized)
        if reason is not None:
            compatibility.append(
                {
                    "input": str(module_code),
                    "decision": "ignored_module_code_alias",
                    "reason": reason,
                }
            )
            return None
        return str(module_code).strip()

    def _tplus_list_body(
        self,
        body: Any,
        *,
        page_size: int,
        page_index: int,
    ) -> dict[str, Any]:
        copied_body = copy.deepcopy(body) if isinstance(body, dict) else {}
        param = copied_body.get("param")
        if not isinstance(param, dict):
            param = {}
            copied_body["param"] = param
        param["pageSize"] = page_size
        param["pageIndex"] = page_index
        if not isinstance(param.get("paramDic"), dict):
            param["paramDic"] = {}
        return copied_body

    def _inject_tplus_list_filters(
        self,
        body: dict[str, Any],
        filters: dict[str, Any],
        query_fields: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        param = body["param"]
        param_dic = param["paramDic"]
        matched_filter_fields: list[dict[str, str]] = []
        unmatched_filters: list[str] = []
        for requested, value in filters.items():
            requested_text = str(requested).strip()
            match = self._find_display_field_match(requested_text, query_fields)
            if match is None:
                unmatched_filters.append(requested_text)
                continue
            field_name = str(match["field"])
            param_dic[field_name] = value
            matched_filter_fields.append(
                {
                    "requested": requested_text,
                    "field": field_name,
                    "label": str(match["label"]),
                }
            )
        if unmatched_filters:
            raise ValueError(
                f"Unmatched filter fields: {', '.join(unmatched_filters)}"
            )
        return matched_filter_fields
```

- [ ] **Step 4: Run the new tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest tests.test_client.ClientTests.test_query_tplus_voucher_list_smart_resolves_template_and_generates_body tests.test_client.ClientTests.test_safe_query_tplus_voucher_list_smart_wraps_missing_template
```

Expected: both tests pass.

- [ ] **Step 5: Run the existing client suite**

Run:

```bash
.venv/bin/python -m unittest tests.test_client
```

Expected: all client tests pass.

- [ ] **Step 6: Commit client implementation**

Run:

```bash
git add src/chanjet_tcloud_mcp/client.py tests/test_client.py
git commit -m "feat: add smart T+ voucher list query"
```

## Task 3: MCP Tool Wrapper

**Files:**
- Modify: `src/chanjet_tcloud_mcp/server.py`

- [ ] **Step 1: Add the MCP wrapper**

Insert this wrapper after `query_tplus_voucher_list` in `src/chanjet_tcloud_mcp/server.py`:

```python
@mcp.tool()
def query_tplus_voucher_list_smart(
    voucher_name: str,
    intent: str | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
    page_size: int = 20,
    page_index: int = 1,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    parent_code: str | None = None,
    module_code: str | None = None,
    api_name: str | None = None,
    path: str | None = None,
    method: str | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Query a T+ voucher list from natural voucher name and list intent.

    Use this for requests like 查询所有生产加工单. The service resolves bizCode,
    finds the official list-query template, builds pageSize/pageIndex/paramDic,
    resolves display_fields, and calls the T+ API.
    """
    return client.safe_query_tplus_voucher_list_smart(
        voucher_name=voucher_name,
        intent=intent,
        filters=filters,
        display_fields=display_fields,
        page_size=page_size,
        page_index=page_index,
        body_overrides=body_overrides,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        path=path,
        method=method,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )
```

- [ ] **Step 2: Verify server import**

Run:

```bash
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
```

Expected output:

```text
chanjet-tcloud
```

- [ ] **Step 3: Commit server wrapper**

Run:

```bash
git add src/chanjet_tcloud_mcp/server.py
git commit -m "feat: expose smart T+ voucher list tool"
```

## Task 4: Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add README section**

Insert this section before the existing `query_tplus_voucher_list` section:

````markdown
`query_tplus_voucher_list_smart`

自然语言 T+ 单据列表查询工具。推荐用于“查生产加工单列表”“查询所有销货单”这类请求。服务会自动识别 `列表`、`查询`、`所有`、`全部` 等意图，解析单据 `bizCode`，搜索官方文档中的列表查询接口，生成分页和查询体，再调用 T+ 业务接口。

参数示例：

```json
{
  "voucher_name": "生产加工单",
  "intent": "查询所有",
  "module_code": "ManufactureOrderOpenApi",
  "filters": {
    "单据编号": "MO-001"
  },
  "display_fields": ["单据编号", "数量"],
  "page_size": 50,
  "page_index": 1,
  "account_alias": "company-a"
}
```

处理规则：

1. `voucher_name` 先通过官方单据类型文档解析 `bizCode`，官方缺失时使用少量稳定兜底映射，例如 `生产加工单 -> MP05`。
2. 工具会搜索官方文档并优先选择 `FindVoucherList` 或名称包含“列表查询”的接口。
3. `filters` 的中文字段会按查询项解析并写入 `body.param.paramDic`。
4. `display_fields` 会按栏目项解析并写入 `body.param.selectFields`。
5. `page_size` 和 `page_index` 会写入 `body.param.pageSize` 和 `body.param.pageIndex`。
6. 如果误传 `module_code: "ManufactureOrderOpenApi"`，工具会把它当作接口类名兼容处理，继续按 `voucher_name` 搜索官方文档。

返回值包含实际业务响应、选中的官方模板、最终请求体和解析过程：

```json
{
  "ok": true,
  "data": {
    "data": {},
    "template": {},
    "request": {
      "path": "/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
      "method": "POST",
      "body": {
        "param": {
          "pageSize": 50,
          "pageIndex": 1,
          "paramDic": {
            "Code": "MO-001"
          },
          "selectFields": ["Code", "Quantity"]
        }
      }
    },
    "resolved": {
      "biz_code": "MP05",
      "biz_code_source": "fallback",
      "matched_filter_fields": [],
      "matched_display_fields": []
    }
  }
}
```
````

- [ ] **Step 2: Verify Markdown fence nesting**

Run:

```bash
python3 - <<'PY'
from pathlib import Path
text = Path("README.md").read_text()
if text.count("```") % 2:
    raise SystemExit("Unbalanced markdown fences")
print("README fences balanced")
PY
```

Expected output:

```text
README fences balanced
```

- [ ] **Step 3: Commit documentation**

Run:

```bash
git add README.md
git commit -m "docs: document smart T+ voucher list query"
```

## Task 5: Final Verification

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run full test discovery**

Run:

```bash
.venv/bin/python -m unittest discover -s tests
```

Expected: all tests pass.

- [ ] **Step 2: Run server import smoke test**

Run:

```bash
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
```

Expected output:

```text
chanjet-tcloud
```

- [ ] **Step 3: Check working tree**

Run:

```bash
git status --short
```

Expected: no output.

- [ ] **Step 4: Report result**

Report the final commit range and verification commands. Mention that the new tool is `query_tplus_voucher_list_smart` and that it handles `生产加工单 -> MP05`, `FindVoucherList`, `paramDic/selectFields`, and `ManufactureOrderOpenApi` compatibility.
