# All-Product Smart API Call Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a unified `call_api_smart` MCP tool that intelligently calls every supported Chanjet product and resolves user-provided Chinese field names into real API request fields before sending requests.

**Architecture:** Reuse the existing official-template flow and `_call_api_by_product` router. Add a shared smart-call implementation in `ChanjetTCloudClient` that copies the official request template, resolves `fields` through API-document metadata or exact request keys, applies T+ special resolution when needed, deep-merges explicit body overrides last, and returns the final request plus resolution metadata. Keep `call_tplus_api_smart` as a compatibility wrapper around the shared implementation.

**Tech Stack:** Python 3.10+, `unittest`, existing `FakeTransport`, existing `FastMCP` server wrapper.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py` for `call_api_smart`, `safe_call_api_smart`, field alias extraction helpers, field injection helpers, and T+ wrapper delegation.
- Modify `src/chanjet_tcloud_mcp/server.py` to expose `call_api_smart` as an MCP tool.
- Modify `tests/test_client.py` with failing tests for cross-product smart field resolution, unresolved-field errors, exact field fallback, T+ compatibility, and the safe wrapper.
- Modify `README.md` to document the all-product smart calling flow and clarify that Chinese fields are resolved before calls.

## Task 1: Cross-Product Smart-Call Tests

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Add failing tests for non-T+ Chinese field resolution and exact field fallback**

Insert these tests after `test_call_api_template_routes_to_matching_product_call` in `tests/test_client.py`:

```python
    def test_call_api_smart_resolves_chinese_fields_for_hyc_template(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "好业财 / 基础档案 / 仓库",
                        "moduleName": "仓库",
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库新增",
                                "apiUrl": "/accounting/openapi/cc/warehouse/create/123",
                                "requestMethod": "POST",
                                "requestBody": {
                                    "code": "",
                                    "name": "",
                                    "statusEnum": "A",
                                },
                                "requestParams": [
                                    {"field": "code", "name": "仓库编码"},
                                    {"field": "name", "name": "仓库名称"},
                                    {"field": "statusEnum", "name": "状态"},
                                ],
                            }
                        ],
                    },
                },
                {"code": "0", "data": {"id": "WH001"}},
            ]
        )

        result = client.call_api_smart(
            product="hyc",
            parent_code="zjjcda",
            module_code="ck",
            api_name="新增",
            fields={"仓库编码": "WH001", "仓库名称": "上海仓"},
            body_overrides={"statusEnum": "A"},
        )

        self.assertEqual(result["template"]["api_name"], "仓库新增")
        self.assertEqual(result["resolved"]["product_code"], "zplus")
        self.assertEqual(
            result["resolved"]["matched_fields"],
            [
                {"requested": "仓库编码", "field": "code", "path": ["code"]},
                {"requested": "仓库名称", "field": "name", "path": ["name"]},
            ],
        )
        self.assertEqual(result["resolved"]["unmatched_fields"], [])
        self.assertEqual(
            result["request"]["body"],
            {"code": "WH001", "name": "上海仓", "statusEnum": "A"},
        )
        self.assertEqual(
            transport.calls[1]["url"],
            "https://openapi.chanjet.com/accounting/openapi/cc/warehouse/create/123",
        )
        self.assertEqual(
            transport.calls[1]["json_body"],
            {"code": "WH001", "name": "上海仓", "statusEnum": "A"},
        )
        self.assertEqual(result["data"], {"code": "0", "data": {"id": "WH001"}})

    def test_call_api_smart_uses_exact_field_name_fallback(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "documentApiInfoList": [
                            {
                                "apiName": "客户新增",
                                "apiUrl": "/accounting/document/customer/create/123",
                                "requestMethod": "POST",
                                "requestBody": {
                                    "customerCode": "",
                                    "customerName": "",
                                },
                            }
                        ],
                    },
                },
                {"code": "0", "data": {"id": "C001"}},
            ]
        )

        result = client.call_api_smart(
            product="hkj",
            parent_code="jcda",
            module_code="customer",
            api_name="新增",
            fields={"customerCode": "C001", "customerName": "客户A"},
        )

        self.assertEqual(
            result["request"]["body"],
            {"customerCode": "C001", "customerName": "客户A"},
        )
        self.assertEqual(
            result["resolved"]["matched_fields"],
            [
                {
                    "requested": "customerCode",
                    "field": "customerCode",
                    "path": ["customerCode"],
                },
                {
                    "requested": "customerName",
                    "field": "customerName",
                    "path": ["customerName"],
                },
            ],
        )
        self.assertEqual(
            transport.calls[1]["url"],
            "https://openapi.chanjet.com/accounting/document/customer/create/123",
        )
```

- [ ] **Step 2: Run targeted tests to verify they fail**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_call_api_smart_resolves_chinese_fields_for_hyc_template tests.test_client.ClientTests.test_call_api_smart_uses_exact_field_name_fallback -v
```

Expected: both tests fail with `AttributeError: 'ChanjetTCloudClient' object has no attribute 'call_api_smart'`.

## Task 2: Shared Smart-Call Implementation

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Add field metadata constants**

Add these constants near the existing `API_*_KEYS` constants in `src/chanjet_tcloud_mcp/client.py`:

```python
SMART_FIELD_NAME_KEYS = (
    "field",
    "fieldName",
    "FieldName",
    "name",
    "paramName",
    "parameterName",
    "code",
    "key",
    "property",
)
SMART_FIELD_LABEL_KEYS = (
    "label",
    "title",
    "caption",
    "Caption",
    "displayName",
    "paramDesc",
    "description",
    "desc",
    "name",
    "fieldLabel",
    "字段名称",
    "字段名",
    "名称",
    "中文名称",
)
SMART_FIELD_CHILD_KEYS = (
    "children",
    "items",
    "params",
    "parameters",
    "requestParams",
    "requestParameters",
    "fields",
    "columns",
    "properties",
)
```

- [ ] **Step 2: Add `call_api_smart` and `safe_call_api_smart`**

Add this method before `call_tplus_api_smart`:

```python
    def call_api_smart(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        body_overrides: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
        voucher_name: str | None = None,
        biz_code: str | None = None,
        business_type_name: str | None = None,
        business_type: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        template_result = self.get_api_call_template(
            product=product,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
        )
        if not template_result["templates"]:
            raise ValueError("No API template matched the requested module and api_name")

        template = template_result["templates"][0]
        request_args = copy.deepcopy(template["arguments"])
        if method is not None:
            request_args["method"] = method
        if query is not None:
            request_args["query"] = query
        if headers is not None:
            request_args["headers"] = headers
        if account_alias is not None:
            request_args["account_alias"] = account_alias

        body = copy.deepcopy(request_args.get("body"))
        matched_fields: list[dict[str, Any]] = []
        unmatched_fields: list[str] = []
        if fields:
            body, matched_fields, unmatched_fields = self._inject_smart_fields(
                body,
                fields,
                template,
            )
            if unmatched_fields:
                raise ValueError(
                    f"Unmatched smart fields: {', '.join(unmatched_fields)}"
                )

        tplus_resolved: dict[str, Any] = {}
        if template_result["product"]["code"] == TCLOUD_PRODUCT_CODE:
            body, tplus_resolved = self._apply_tplus_smart_fields(
                body=body,
                voucher_name=voucher_name,
                biz_code=biz_code,
                business_type_name=business_type_name,
                business_type=business_type,
                filters=filters,
                display_fields=display_fields,
                headers=headers,
                account_alias=account_alias,
            )

        if body_overrides is not None:
            body = self._deep_merge_values(body, body_overrides)
        request_args["body"] = body

        response = self._call_api_by_product(
            template_result["product"]["code"],
            path=request_args["path"],
            method=request_args["method"],
            body=request_args.get("body"),
            query=request_args.get("query"),
            headers=request_args.get("headers"),
            account_alias=request_args.get("account_alias"),
        )

        resolved = {
            "product_code": template_result["product"]["code"],
            "matched_fields": matched_fields,
            "unmatched_fields": unmatched_fields,
        }
        resolved.update(tplus_resolved)
        return {
            "template": template,
            "resolved": resolved,
            "request": request_args,
            "data": response,
        }
```

Add this safe wrapper near the existing `safe_call_api_template` method:

```python
    def safe_call_api_smart(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        body_overrides: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
        voucher_name: str | None = None,
        biz_code: str | None = None,
        business_type_name: str | None = None,
        business_type: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.call_api_smart(
                    product=product,
                    parent_code=parent_code,
                    module_code=module_code,
                    api_name=api_name,
                    fields=fields,
                    body_overrides=body_overrides,
                    query=query,
                    headers=headers,
                    account_alias=account_alias,
                    method=method,
                    voucher_name=voucher_name,
                    biz_code=biz_code,
                    business_type_name=business_type_name,
                    business_type=business_type,
                    filters=filters,
                    display_fields=display_fields,
                )
            )
        except Exception as exc:
            return self.tool_error(
                exc,
                hint=(
                    "Use exact API field names or call get_api_call_template/"
                    "search_api_templates to inspect available fields."
                ),
            )
```

- [ ] **Step 3: Add smart field extraction and injection helpers**

Add these helpers near `_deep_merge_values`:

```python
    def _inject_smart_fields(
        self,
        body: Any,
        fields: dict[str, Any],
        template: dict[str, Any],
    ) -> tuple[Any, list[dict[str, Any]], list[str]]:
        if body is None:
            body = {}
        if not isinstance(body, dict):
            raise ValueError("Request body must be an object to inject smart fields")
        updated_body = copy.deepcopy(body)
        aliases = self._smart_field_aliases(template)
        matched_fields: list[dict[str, Any]] = []
        unmatched_fields: list[str] = []

        for requested, value in fields.items():
            requested_text = str(requested).strip()
            normalized = self._normalize_match_value(requested_text)
            match = aliases.get(normalized)
            if match is None:
                unmatched_fields.append(requested_text)
                continue
            self._set_body_path(updated_body, match["path"], value)
            matched_fields.append(
                {
                    "requested": requested_text,
                    "field": match["field"],
                    "path": match["path"],
                }
            )

        return updated_body, matched_fields, unmatched_fields

    def _smart_field_aliases(self, template: dict[str, Any]) -> dict[str, dict[str, Any]]:
        aliases: dict[str, dict[str, Any]] = {}

        def register(path: list[str], field: str, labels: list[Any]) -> None:
            if not path or not field:
                return
            match = {"field": field, "path": path}
            for label in [field, *labels]:
                normalized = self._normalize_match_value(label)
                if normalized and normalized not in aliases:
                    aliases[normalized] = match

        def collect(item: Any, current_path: list[str] | None = None) -> None:
            current_path = current_path or []
            if isinstance(item, list):
                for child in item:
                    collect(child, current_path)
                return
            if not isinstance(item, dict):
                return

            field = self._first_mapping_value(item, SMART_FIELD_NAME_KEYS)
            labels = [
                value
                for key in SMART_FIELD_LABEL_KEYS
                for value in [item.get(key)]
                if value is not None
            ]
            if field is not None:
                field_text = str(field).strip()
                path = [*current_path, field_text] if current_path else [field_text]
                register(path, field_text, labels)

            for key, value in item.items():
                if key in SMART_FIELD_CHILD_KEYS:
                    collect(value, current_path)
                elif isinstance(value, dict):
                    collect(value, current_path)
                elif isinstance(value, list):
                    collect(value, current_path)

        collect(template.get("raw", template))
        body = template.get("body")
        if isinstance(body, dict):
            default_parent = ["param"] if isinstance(body.get("param"), dict) else []
            for key in body.get("param", body).keys():
                field_path = [*default_parent, str(key)]
                register(field_path, str(key), [])
        return aliases

    def _set_body_path(
        self,
        body: dict[str, Any],
        path: list[str],
        value: Any,
    ) -> None:
        target = body
        for key in path[:-1]:
            next_value = target.get(key)
            if not isinstance(next_value, dict):
                next_value = {}
                target[key] = next_value
            target = next_value
        target[path[-1]] = value
```

- [ ] **Step 4: Run targeted tests to verify green**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_call_api_smart_resolves_chinese_fields_for_hyc_template tests.test_client.ClientTests.test_call_api_smart_uses_exact_field_name_fallback -v
```

Expected: both tests pass.

- [ ] **Step 5: Commit Task 2**

Run:

```bash
git add src/chanjet_tcloud_mcp/client.py tests/test_client.py
git commit -m "Add all-product smart field calls"
```

## Task 3: Unresolved Field Errors

**Files:**
- Modify: `tests/test_client.py`
- Modify: `src/chanjet_tcloud_mcp/client.py`

- [ ] **Step 1: Add failing safe-wrapper test**

Insert this test after the exact field fallback test:

```python
    def test_safe_call_api_smart_wraps_unmatched_chinese_field(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库新增",
                                "apiUrl": "/accounting/openapi/cc/warehouse/create/123",
                                "requestMethod": "POST",
                                "requestBody": {"code": ""},
                                "requestParams": [
                                    {"field": "code", "name": "仓库编码"},
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.safe_call_api_smart(
            product="hyc",
            parent_code="zjjcda",
            module_code="ck",
            api_name="新增",
            fields={"不存在字段": "x"},
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_argument")
        self.assertIn("Unmatched smart fields", result["error"]["message"])
        self.assertIn("不存在字段", result["error"]["message"])
        self.assertIn("get_api_call_template", result["error"]["hint"])
        self.assertEqual(len(transport.calls), 1)
```

- [ ] **Step 2: Run the new test to verify it fails if Task 2 did not include safe error wrapping**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_safe_call_api_smart_wraps_unmatched_chinese_field -v
```

Expected before implementation is complete: failure because `safe_call_api_smart` is missing or does not return the expected hint.

- [ ] **Step 3: Ensure `safe_call_api_smart` uses the configured hint**

Confirm `src/chanjet_tcloud_mcp/client.py` contains:

```python
        except Exception as exc:
            return self.tool_error(
                exc,
                hint=(
                    "Use exact API field names or call get_api_call_template/"
                    "search_api_templates to inspect available fields."
                ),
            )
```

- [ ] **Step 4: Run unresolved-field test to verify green**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_safe_call_api_smart_wraps_unmatched_chinese_field -v
```

Expected: test passes.

- [ ] **Step 5: Commit Task 3**

Run:

```bash
git add src/chanjet_tcloud_mcp/client.py tests/test_client.py
git commit -m "Handle unresolved smart fields"
```

## Task 4: T+ Compatibility Through Shared Smart Path

**Files:**
- Modify: `tests/test_client.py`
- Modify: `src/chanjet_tcloud_mcp/client.py`

- [ ] **Step 1: Add failing unified T+ smart-call test**

Insert this test near the existing T+ smart-call tests:

```python
    def test_call_api_smart_preserves_tplus_natural_input_resolution(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "T+Cloud / 销售 / 销货单列表",
                        "moduleName": "销货单列表",
                        "documentApiInfoList": [
                            {
                                "apiName": "销货单列表查询",
                                "apiUrl": "/tplus/api/v2/saleDelivery/Query",
                                "requestMethod": "POST",
                                "requestBody": {"param": {"pageIndex": 1}},
                            }
                        ],
                    },
                },
                {
                    "result": True,
                    "error": None,
                    "value": {"rows": [{"code": "SA04", "name": "销货单"}]},
                },
                {
                    "result": True,
                    "error": None,
                    "value": {"rows": [{"code": "02", "name": "采购退货"}]},
                },
                {
                    "code": "0",
                    "data": {"items": [{"FieldName": "CustomerName", "Caption": "客户"}]},
                },
                {
                    "code": "0",
                    "data": {"columns": [{"FieldName": "Code", "Caption": "单据编号"}]},
                },
                {"code": "0", "data": [{"Code": "SA-001"}]},
            ]
        )

        result = client.call_api_smart(
            product="tplus",
            parent_code="t+xs",
            module_code="saleDelivery",
            api_name="列表查询",
            voucher_name="销货单",
            business_type_name="采购退货",
            filters={"客户": "客户A"},
            display_fields=["单据编号"],
            body_overrides={"param": {"pageSize": 10}},
        )

        self.assertEqual(
            transport.calls[5]["json_body"],
            {
                "param": {
                    "pageIndex": 1,
                    "BusinessType": "02",
                    "CustomerName": "客户A",
                    "selectFields": ["Code"],
                    "pageSize": 10,
                }
            },
        )
        self.assertEqual(result["resolved"]["product_code"], "tcloud")
        self.assertEqual(result["resolved"]["biz_code"], "SA04")
        self.assertEqual(result["resolved"]["business_type"], "02")
```

- [ ] **Step 2: Run unified T+ test to verify it fails before shared T+ helper exists**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_call_api_smart_preserves_tplus_natural_input_resolution -v
```

Expected: failure because `_apply_tplus_smart_fields` is not implemented or T+ resolution is not wired through `call_api_smart`.

- [ ] **Step 3: Extract T+ special handling into `_apply_tplus_smart_fields` and delegate `call_tplus_api_smart`**

Add this helper in `src/chanjet_tcloud_mcp/client.py` near `_inject_smart_fields`:

```python
    def _apply_tplus_smart_fields(
        self,
        *,
        body: Any,
        voucher_name: str | None,
        biz_code: str | None,
        business_type_name: str | None,
        business_type: str | None,
        filters: dict[str, Any] | None,
        display_fields: list[str] | None,
        headers: dict[str, str] | None,
        account_alias: str | None,
    ) -> tuple[Any, dict[str, Any]]:
        resolved_biz_code = biz_code
        resolved_business_type = business_type
        reference_lookup: dict[str, Any] | None = None

        if voucher_name or business_type_name:
            reference_lookup = self.get_tplus_reference_codes()
        if not resolved_biz_code and voucher_name and reference_lookup is not None:
            resolved_biz_code = self._resolve_reference_code(
                reference_lookup["voucher_types"],
                voucher_name,
                label="voucher type",
            )
        if (
            not resolved_business_type
            and business_type_name
            and reference_lookup is not None
        ):
            resolved_business_type = self._resolve_reference_code(
                reference_lookup["business_types"],
                business_type_name,
                label="business type",
            )

        field_lookup: dict[str, Any] | None = None
        if filters or display_fields:
            if not resolved_biz_code:
                raise ValueError(
                    "biz_code or voucher_name is required to resolve filters or display_fields"
                )
            field_lookup = self.get_tplus_voucher_list_fields(
                biz_code=resolved_biz_code,
                headers=headers,
                account_alias=account_alias,
            )

        matched_filter_fields: list[dict[str, str]] = []
        matched_display_fields: list[dict[str, str]] = []
        if filters:
            body = self._ensure_param_body(body)
            param = body["param"]
            unmatched_filters: list[str] = []
            for requested, value in filters.items():
                requested_text = str(requested).strip()
                match = self._find_display_field_match(
                    requested_text,
                    field_lookup["query_fields"] if field_lookup else [],
                )
                if match is None:
                    unmatched_filters.append(requested_text)
                    continue
                field_name = str(match["field"])
                param[field_name] = value
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

        if resolved_business_type:
            body = self._ensure_param_body(body)
            body["param"]["BusinessType"] = resolved_business_type

        if display_fields:
            matched_display_fields, unmatched_display_fields = self._match_display_fields(
                display_fields,
                field_lookup["display_fields"] if field_lookup else [],
            )
            if unmatched_display_fields:
                raise ValueError(
                    f"Unmatched display fields: {', '.join(unmatched_display_fields)}"
                )
            body = self._inject_display_fields(
                body,
                [field["field"] for field in matched_display_fields],
            )

        return body, {
            "biz_code": resolved_biz_code,
            "voucher_name": voucher_name,
            "business_type": resolved_business_type,
            "business_type_name": business_type_name,
            "matched_filter_fields": matched_filter_fields,
            "matched_display_fields": matched_display_fields,
            "reference_source_docs": (
                reference_lookup.get("source_docs") if reference_lookup else None
            ),
            "field_source_doc": (
                field_lookup.get("source_doc") if field_lookup else None
            ),
        }
```

Replace `call_tplus_api_smart` with a delegation wrapper:

```python
    def call_tplus_api_smart(
        self,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        voucher_name: str | None = None,
        biz_code: str | None = None,
        business_type_name: str | None = None,
        business_type: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        body_overrides: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
    ) -> dict[str, Any]:
        return self.call_api_smart(
            product=TCLOUD_PRODUCT_CODE,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
            body_overrides=body_overrides,
            query=query,
            headers=headers,
            account_alias=account_alias,
            method=method,
            voucher_name=voucher_name,
            biz_code=biz_code,
            business_type_name=business_type_name,
            business_type=business_type,
            filters=filters,
            display_fields=display_fields,
        )
```

- [ ] **Step 4: Run T+ compatibility tests to verify green**

Run:

```bash
PYTHONPATH=src python3 -m unittest tests.test_client.ClientTests.test_call_api_smart_preserves_tplus_natural_input_resolution tests.test_client.ClientTests.test_call_tplus_api_smart_uses_template_and_resolves_natural_inputs tests.test_client.ClientTests.test_call_tplus_api_smart_rejects_unmatched_filter tests.test_client.ClientTests.test_safe_call_tplus_api_smart_wraps_unmatched_filter -v
```

Expected: all four tests pass.

- [ ] **Step 5: Commit Task 4**

Run:

```bash
git add src/chanjet_tcloud_mcp/client.py tests/test_client.py
git commit -m "Share T+ smart call resolution"
```

## Task 5: MCP Tool and Documentation

**Files:**
- Modify: `src/chanjet_tcloud_mcp/server.py`
- Modify: `README.md`
- Test: `tests/test_client.py`

- [ ] **Step 1: Add server wrapper**

Add this MCP tool before `call_api_template` in `src/chanjet_tcloud_mcp/server.py`:

```python
@mcp.tool()
def call_api_smart(
    product: str,
    parent_code: str,
    module_code: str,
    api_name: str | None = None,
    fields: dict[str, Any] | None = None,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
    method: str | None = None,
    voucher_name: str | None = None,
    biz_code: str | None = None,
    business_type_name: str | None = None,
    business_type: str | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Call any supported product API from the official template.

    User-facing Chinese field names in fields are resolved to real API request
    fields before the request is sent. T+ calls also support voucher/business
    type and voucher list field resolution.
    """
    return client.safe_call_api_smart(
        product=product,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        fields=fields,
        body_overrides=body_overrides,
        query=query,
        headers=headers,
        account_alias=account_alias,
        method=method,
        voucher_name=voucher_name,
        biz_code=biz_code,
        business_type_name=business_type_name,
        business_type=business_type,
        filters=filters,
        display_fields=display_fields,
    )
```

- [ ] **Step 2: Update README recommended flow**

In `README.md`, change the recommended client flow from `call_api_template` as the primary caller to `call_api_smart`. Add this example near the existing `call_api_template` section:

    `call_api_smart`

    推荐优先使用的智能调用工具。它会先读取官方接口模板，再把用户传入的中文字段解析成真实接口字段，最后自动路由到对应产品接口。解析不到字段时返回统一错误结构，不会静默调用错误请求。

    参数示例：

    ```json
    {
      "product": "hyc",
      "parent_code": "zjjcda",
      "module_code": "ck",
      "api_name": "新增",
      "fields": {
        "仓库编码": "WH001",
        "仓库名称": "上海仓"
      },
      "body_overrides": {
        "statusEnum": "A"
      },
      "account_alias": "company-a"
    }
    ```

    T+ 接口还支持 `voucher_name`、`business_type_name`、`filters` 和 `display_fields`，用于自动解析单据类型、业务类型、查询项和显示栏目。

- [ ] **Step 3: Run import smoke test**

Run:

```bash
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
```

Expected output:

```text
chanjet-tcloud
```

- [ ] **Step 4: Commit Task 5**

Run:

```bash
git add src/chanjet_tcloud_mcp/server.py README.md
git commit -m "Expose all-product smart API tool"
```

## Task 6: Full Verification

**Files:**
- Verify: entire repository

- [ ] **Step 1: Run the full unit suite**

Run:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
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

- [ ] **Step 3: Run whitespace check**

Run:

```bash
git diff --check
```

Expected: no output and exit code 0.

- [ ] **Step 4: Inspect final git state**

Run:

```bash
git status --short --branch
```

Expected: branch shows only intentional committed changes or a clean worktree after final commit.
