# Natural API Router Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `call_natural`, a deterministic natural-language routing tool that parses user text, ranks candidate Chanjet API routes across all supported products, calls only high-confidence routes, and returns suggestions for low-confidence cases.

**Architecture:** Keep `server.py` thin and implement parsing/routing in `ChanjetTCloudClient`. Reuse existing `query_tplus_voucher_list_smart`, `search_api_templates`, `call_api_smart`, product metadata, official document fetching, field injection, token refresh, and error envelopes. The first implementation uses keyword parsing and confidence scoring only; it does not embed or call an LLM.

**Tech Stack:** Python 3.10+, standard-library `unittest`, existing fake `JsonTransport`, MCP `FastMCP`.

---

## File Structure

- Modify `src/chanjet_tcloud_mcp/client.py`: add natural router constants, parsing helpers, candidate ranking helpers, `call_natural`, and `safe_call_natural`.
- Modify `src/chanjet_tcloud_mcp/server.py`: expose `call_natural` as a thin MCP wrapper.
- Modify `tests/test_client.py`: add TDD tests for invalid input, T+ list routing, low-confidence suggestions, dry-run behavior, HYC template routing, and multi-candidate suggestions.
- Modify `README.md`: document `call_natural` as the highest-level LLM-facing entry point.

## Task 1: Client RED Tests

**Files:**
- Modify: `tests/test_client.py`

- [ ] **Step 1: Add invalid-input and low-confidence tests**

Insert these tests after `test_safe_query_tplus_voucher_list_smart_wraps_missing_template` in `tests/test_client.py`:

```python
    def test_safe_call_natural_wraps_empty_input(self):
        client, _transport = self.make_client([])

        result = client.safe_call_natural(user_input="   ")

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_argument")
        self.assertIn("user_input is required", result["error"]["message"])

    def test_call_natural_suggests_when_product_is_missing(self):
        client, transport = self.make_client([])

        result = client.call_natural(user_input="新增仓库")

        self.assertEqual(result["decision"], "suggest")
        self.assertEqual(result["selected_tool"], None)
        self.assertLess(result["confidence"], 0.75)
        self.assertIn("product", result["missing"])
        self.assertEqual(result["parsed_intent"]["action"], "create")
        self.assertEqual(result["parsed_intent"]["business_object"], "仓库")
        self.assertEqual(len(transport.calls), 0)
```

- [ ] **Step 2: Run invalid-input and low-confidence tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest tests.test_client.ClientTests.test_safe_call_natural_wraps_empty_input tests.test_client.ClientTests.test_call_natural_suggests_when_product_is_missing
```

Expected: FAIL with `AttributeError` because `safe_call_natural` and `call_natural` do not exist.

- [ ] **Step 3: Add T+ natural list routing test**

Insert this test after the low-confidence test:

```python
    def test_call_natural_routes_tplus_voucher_list_request(self):
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

        result = client.call_natural(
            user_input="查询所有生产加工单，显示单据编号和数量",
            filters={"单据编号": "MO-001"},
            page_size=50,
            page_index=2,
        )

        self.assertEqual(result["decision"], "call")
        self.assertEqual(result["selected_tool"], "query_tplus_voucher_list_smart")
        self.assertGreaterEqual(result["confidence"], 0.75)
        self.assertEqual(result["parsed_intent"]["product"], "tcloud")
        self.assertEqual(result["parsed_intent"]["action"], "list")
        self.assertEqual(result["parsed_intent"]["voucher_name"], "生产加工单")
        self.assertEqual(result["parsed_intent"]["display_fields"], ["单据编号", "数量"])
        self.assertEqual(result["request"]["body"]["param"]["paramDic"], {"Code": "MO-001"})
        self.assertEqual(result["request"]["body"]["param"]["selectFields"], ["Code", "Quantity"])
        self.assertEqual(result["data"], {"code": "0", "data": [{"Code": "MO-001", "Quantity": 3}]})
        self.assertEqual(
            transport.calls[-1]["url"],
            "https://openapi.chanjet.com/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
        )
```

- [ ] **Step 4: Add generic HYC dry-run and call tests**

Insert these tests after the T+ routing test:

```python
    def test_call_natural_dry_run_returns_hyc_route_without_business_call(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "zplus",
                        "children": [
                            {
                                "moduleCode": "zjjcda",
                                "moduleName": "基础档案",
                                "children": [{"moduleCode": "ck", "moduleName": "仓库"}],
                            }
                        ],
                    },
                },
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
                                "requestBody": {"code": "", "name": "", "statusEnum": "A"},
                                "requestParams": [
                                    {"field": "code", "name": "编码"},
                                    {"field": "name", "name": "名称"},
                                ],
                            }
                        ],
                    },
                },
            ]
        )

        result = client.call_natural(
            user_input="好业财新增仓库，编码 WH001，名称 上海仓",
            dry_run=True,
        )

        self.assertEqual(result["decision"], "call")
        self.assertEqual(result["selected_tool"], "call_api_smart")
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["parsed_intent"]["product"], "zplus")
        self.assertEqual(result["parsed_intent"]["action"], "create")
        self.assertEqual(result["parsed_intent"]["business_object"], "仓库")
        self.assertEqual(result["parsed_intent"]["fields"], {"编码": "WH001", "名称": "上海仓"})
        self.assertEqual(result["request"]["path"], "/accounting/openapi/cc/warehouse/create/123")
        self.assertEqual(len(transport.calls), 2)

    def test_call_natural_calls_hyc_create_when_single_template_matches(self):
        api_doc = {
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
                        "requestBody": {"code": "", "name": "", "statusEnum": "A"},
                        "requestParams": [
                            {"field": "code", "name": "编码"},
                            {"field": "name", "name": "名称"},
                        ],
                    }
                ],
            },
        }
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "zplus",
                        "children": [
                            {
                                "moduleCode": "zjjcda",
                                "moduleName": "基础档案",
                                "children": [{"moduleCode": "ck", "moduleName": "仓库"}],
                            }
                        ],
                    },
                },
                api_doc,
                api_doc,
                {"code": "0", "data": {"id": "WH001"}},
            ]
        )

        result = client.call_natural(user_input="好业财新增仓库，编码 WH001，名称 上海仓")

        self.assertEqual(result["decision"], "call")
        self.assertEqual(result["selected_tool"], "call_api_smart")
        self.assertEqual(result["request"]["body"], {"code": "WH001", "name": "上海仓", "statusEnum": "A"})
        self.assertEqual(
            transport.calls[-1]["url"],
            "https://openapi.chanjet.com/accounting/openapi/cc/warehouse/create/123",
        )
        self.assertEqual(result["data"], {"code": "0", "data": {"id": "WH001"}})
```

- [ ] **Step 5: Add multi-candidate suggestion test**

Insert this test after the HYC call test:

```python
    def test_call_natural_suggests_when_multiple_templates_match(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "zplus",
                        "children": [
                            {
                                "moduleCode": "zjjcda",
                                "moduleName": "基础档案",
                                "children": [{"moduleCode": "ck", "moduleName": "仓库"}],
                            }
                        ],
                    },
                },
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
                                "requestBody": {"code": "", "name": ""},
                            },
                            {
                                "apiName": "仓库快速新增",
                                "apiUrl": "/accounting/openapi/cc/warehouse/quickCreate/123",
                                "requestMethod": "POST",
                                "requestBody": {"code": "", "name": ""},
                            },
                        ],
                    },
                },
            ]
        )

        result = client.call_natural(user_input="好业财新增仓库，编码 WH001，名称 上海仓")

        self.assertEqual(result["decision"], "suggest")
        self.assertEqual(result["selected_tool"], None)
        self.assertGreaterEqual(len(result["candidates"]), 2)
        self.assertEqual(len(transport.calls), 2)
        self.assertTrue(all(candidate["tool"] == "call_api_smart" for candidate in result["candidates"]))
```

- [ ] **Step 6: Run all new tests to verify RED**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_client.ClientTests.test_safe_call_natural_wraps_empty_input \
  tests.test_client.ClientTests.test_call_natural_suggests_when_product_is_missing \
  tests.test_client.ClientTests.test_call_natural_routes_tplus_voucher_list_request \
  tests.test_client.ClientTests.test_call_natural_dry_run_returns_hyc_route_without_business_call \
  tests.test_client.ClientTests.test_call_natural_calls_hyc_create_when_single_template_matches \
  tests.test_client.ClientTests.test_call_natural_suggests_when_multiple_templates_match
```

Expected: FAIL with `AttributeError` because `call_natural` and `safe_call_natural` do not exist.

- [ ] **Step 7: Commit RED tests**

Run:

```bash
git add tests/test_client.py
git commit -m "test: cover natural API router"
```

## Task 2: Client Natural Router

**Files:**
- Modify: `src/chanjet_tcloud_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] **Step 1: Add constants and import**

In `src/chanjet_tcloud_mcp/client.py`, add `import re` after `import hashlib`.

Add these constants after `PRODUCT_ALIASES`:

```python
NATURAL_PRODUCT_ALIASES = {
    alias.casefold(): product_code
    for product_code, metadata in PRODUCT_METADATA.items()
    for alias in metadata["aliases"]
}
NATURAL_PRODUCT_ALIASES.update(
    {
        "t+cloud": TCLOUD_PRODUCT_CODE,
        "好业财": HYC_PRODUCT_CODE,
        "好生意": HSY_PRODUCT_CODE,
        "易代账": YDZ_PRODUCT_CODE,
        "好会计": HKJ_PRODUCT_CODE,
    }
)
NATURAL_ACTION_ALIASES = {
    "list": ("列表", "查询", "查", "所有", "全部", "list", "query", "all"),
    "create": ("新增", "创建", "添加", "保存", "create", "add", "save"),
    "update": ("修改", "更新", "编辑", "update", "edit"),
    "delete": ("删除", "移除", "作废", "delete", "remove"),
    "audit": ("审核", "审批", "通过", "audit", "approve"),
    "unaudit": ("弃审", "反审核", "取消审核", "unaudit", "unapprove"),
}
NATURAL_ACTION_API_NAMES = {
    "list": "查询",
    "create": "新增",
    "update": "修改",
    "delete": "删除",
    "audit": "审核",
    "unaudit": "弃审",
}
NATURAL_CALL_THRESHOLD = 0.75
NATURAL_CLOSE_CANDIDATE_DELTA = 0.10
```

- [ ] **Step 2: Add public client methods**

Add these methods after `safe_query_tplus_voucher_list_smart`:

```python
    def call_natural(
        self,
        user_input: str,
        *,
        product: str | None = None,
        dry_run: bool = False,
        fields: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        body_overrides: Any = None,
        page_size: int = 20,
        page_index: int = 1,
        headers: dict[str, str] | None = None,
        query: dict[str, Any] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        parsed = self._parse_natural_intent(
            user_input,
            product=product,
            fields=fields,
            filters=filters,
            display_fields=display_fields,
        )
        if not parsed["user_input"]:
            raise ValueError("user_input is required")

        if (
            parsed["action"] == "list"
            and parsed["product"] in (None, TCLOUD_PRODUCT_CODE)
            and parsed["business_object"]
            and self._natural_object_can_default_to_tplus(parsed["business_object"])
        ):
            parsed["product"] = TCLOUD_PRODUCT_CODE
            parsed["voucher_name"] = parsed["business_object"]
            parsed["product_source"] = parsed["product_source"] or "tplus_voucher_default"

        if not parsed["product"]:
            return self._natural_suggestion(
                parsed,
                confidence=self._natural_confidence(parsed, template_found=False),
                missing=["product"],
                reason="Product could not be identified from user_input.",
            )

        if parsed["action"] == "list" and parsed["product"] == TCLOUD_PRODUCT_CODE and parsed["voucher_name"]:
            return self._call_natural_tplus_list(
                parsed,
                dry_run=dry_run,
                filters=filters,
                body_overrides=body_overrides,
                page_size=page_size,
                page_index=page_index,
                headers=headers,
                query=query,
                account_alias=account_alias,
            )

        if not parsed["action"] or not parsed["business_object"]:
            missing = []
            if not parsed["action"]:
                missing.append("action")
            if not parsed["business_object"]:
                missing.append("business_object")
            return self._natural_suggestion(
                parsed,
                confidence=self._natural_confidence(parsed, template_found=False),
                missing=missing,
                reason="Action or business object could not be identified.",
            )

        return self._call_natural_template(
            parsed,
            dry_run=dry_run,
            body_overrides=body_overrides,
            headers=headers,
            query=query,
            account_alias=account_alias,
        )

    def safe_call_natural(
        self,
        user_input: str,
        *,
        product: str | None = None,
        dry_run: bool = False,
        fields: dict[str, Any] | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        body_overrides: Any = None,
        page_size: int = 20,
        page_index: int = 1,
        headers: dict[str, str] | None = None,
        query: dict[str, Any] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.call_natural(
                    user_input=user_input,
                    product=product,
                    dry_run=dry_run,
                    fields=fields,
                    filters=filters,
                    display_fields=display_fields,
                    body_overrides=body_overrides,
                    page_size=page_size,
                    page_index=page_index,
                    headers=headers,
                    query=query,
                    account_alias=account_alias,
                )
            )
        except Exception as exc:
            return self.tool_error(
                exc,
                hint="Pass a natural request such as 查询所有生产加工单 or provide product/action hints.",
            )
```

- [ ] **Step 3: Add parsing helpers**

Add these methods near the existing helper methods before `_is_tplus_list_intent`:

```python
    def _parse_natural_intent(
        self,
        user_input: str,
        *,
        product: str | None,
        fields: dict[str, Any] | None,
        filters: dict[str, Any] | None,
        display_fields: list[str] | None,
    ) -> dict[str, Any]:
        text = str(user_input or "").strip()
        product_code, product_source = self._natural_product(text, product)
        action = self._natural_action(text)
        parsed_display_fields = display_fields or self._natural_display_fields(text)
        parsed_fields = fields or self._natural_key_values(text)
        business_object = self._natural_business_object(
            text,
            product_code=product_code,
            action=action,
            display_fields=parsed_display_fields,
            parsed_fields=parsed_fields,
        )
        return {
            "user_input": text,
            "product": product_code,
            "product_source": product_source,
            "action": action,
            "business_object": business_object,
            "voucher_name": business_object if action == "list" else None,
            "fields": parsed_fields,
            "filters": filters or {},
            "display_fields": parsed_display_fields,
            "unresolved_text": text,
        }

    def _natural_product(
        self,
        text: str,
        product_hint: str | None,
    ) -> tuple[str | None, str | None]:
        if product_hint:
            return self._product_metadata(product_hint)["code"], "explicit"
        normalized_text = text.casefold()
        matches: list[str] = []
        for alias, product_code in NATURAL_PRODUCT_ALIASES.items():
            if alias and alias in normalized_text:
                matches.append(product_code)
        unique_matches = []
        for item in matches:
            if item not in unique_matches:
                unique_matches.append(item)
        if len(unique_matches) == 1:
            return unique_matches[0], "user_input"
        return None, None

    def _natural_action(self, text: str) -> str | None:
        raw = text.casefold()
        normalized = self._normalize_match_value(text)
        for action, markers in NATURAL_ACTION_ALIASES.items():
            if any(marker.casefold() in raw or self._normalize_match_value(marker) in normalized for marker in markers):
                return action
        return None

    def _natural_display_fields(self, text: str) -> list[str]:
        marker = "显示"
        if marker not in text:
            return []
        tail = text.split(marker, 1)[1]
        tail = re.split(r"[，,。；;]", tail, maxsplit=1)[0]
        return [
            part.strip()
            for part in re.split(r"[、和及/\\s]+", tail)
            if part.strip()
        ]

    def _natural_key_values(self, text: str) -> dict[str, Any]:
        values: dict[str, Any] = {}
        for part in re.split(r"[，,。；;]", text):
            cleaned = part.strip()
            if not cleaned:
                continue
            match = re.match(r"^([^\\s:：=]+)\\s*[:：= ]\\s*(.+)$", cleaned)
            if not match:
                continue
            key = match.group(1).strip()
            value = match.group(2).strip()
            if key and value and key not in {"显示", "查询", "新增", "创建"}:
                values[key] = value
        return values

    def _natural_business_object(
        self,
        text: str,
        *,
        product_code: str | None,
        action: str | None,
        display_fields: list[str],
        parsed_fields: dict[str, Any],
    ) -> str | None:
        head = re.split(r"[，,。；;]", text, maxsplit=1)[0].strip()
        if "显示" in head:
            head = head.split("显示", 1)[0].strip()
        for metadata in PRODUCT_METADATA.values():
            for alias in metadata["aliases"]:
                head = head.replace(str(alias), "")
            head = head.replace(metadata["name"], "")
        for alias in NATURAL_PRODUCT_ALIASES:
            if any(ord(char) > 127 for char in alias):
                head = head.replace(alias, "")
        markers: list[str] = []
        for items in NATURAL_ACTION_ALIASES.values():
            markers.extend(str(item) for item in items)
        for marker in sorted(markers, key=len, reverse=True):
            head = head.replace(marker, "")
        for field_name in display_fields:
            head = head.replace(field_name, "")
        for key in parsed_fields:
            head = head.replace(key, "")
            head = head.replace(str(parsed_fields[key]), "")
        cleaned = re.sub(r"\\s+", "", head)
        return cleaned or None

    def _natural_object_can_default_to_tplus(self, business_object: str) -> bool:
        normalized = self._normalize_match_value(business_object)
        return any(
            self._normalize_match_value(name) == normalized
            for name in TPLUS_VOUCHER_BIZ_CODE_FALLBACKS
        )
```

- [ ] **Step 4: Add routing helpers**

Add these methods after the parsing helpers:

```python
    def _natural_confidence(
        self,
        parsed: dict[str, Any],
        *,
        template_found: bool,
        field_confidence: bool = False,
    ) -> float:
        score = 0.0
        if parsed.get("product"):
            score += 0.25
        if parsed.get("action"):
            score += 0.20
        if parsed.get("business_object") or parsed.get("voucher_name"):
            score += 0.20
        if template_found:
            score += 0.25
        if field_confidence:
            score += 0.10
        return min(score, 1.0)

    def _natural_suggestion(
        self,
        parsed: dict[str, Any],
        *,
        confidence: float,
        missing: list[str],
        reason: str,
        candidates: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        return {
            "parsed_intent": parsed,
            "confidence": confidence,
            "decision": "suggest",
            "selected_tool": None,
            "candidates": candidates or [],
            "missing": missing,
            "reason": reason,
            "request": None,
            "data": None,
        }

    def _call_natural_tplus_list(
        self,
        parsed: dict[str, Any],
        *,
        dry_run: bool,
        filters: dict[str, Any] | None,
        body_overrides: Any,
        page_size: int,
        page_index: int,
        headers: dict[str, str] | None,
        query: dict[str, Any] | None,
        account_alias: str | None,
    ) -> dict[str, Any]:
        confidence = self._natural_confidence(parsed, template_found=True, field_confidence=bool(parsed["display_fields"] or filters))
        candidate = {
            "tool": "query_tplus_voucher_list_smart",
            "product": TCLOUD_PRODUCT_CODE,
            "action": "list",
            "module": {},
            "api_name": None,
            "path": None,
            "score": confidence,
            "reason": "T+ voucher list request resolved from natural input.",
            "missing": [],
        }
        if dry_run:
            return {
                "parsed_intent": parsed,
                "confidence": confidence,
                "decision": "call",
                "selected_tool": "query_tplus_voucher_list_smart",
                "candidates": [candidate],
                "missing": [],
                "reason": "Dry run selected T+ voucher list route.",
                "dry_run": True,
                "request": {
                    "tool": "query_tplus_voucher_list_smart",
                    "voucher_name": parsed["voucher_name"],
                    "intent": parsed["user_input"],
                    "filters": filters or parsed["filters"],
                    "display_fields": parsed["display_fields"],
                    "page_size": page_size,
                    "page_index": page_index,
                },
                "data": None,
            }
        result = self.query_tplus_voucher_list_smart(
            voucher_name=parsed["voucher_name"],
            intent=parsed["user_input"],
            filters=filters or parsed["filters"],
            display_fields=parsed["display_fields"],
            page_size=page_size,
            page_index=page_index,
            body_overrides=body_overrides,
            headers=headers,
            query=query,
            account_alias=account_alias,
        )
        return {
            "parsed_intent": parsed,
            "confidence": confidence,
            "decision": "call",
            "selected_tool": "query_tplus_voucher_list_smart",
            "candidates": [candidate],
            "missing": [],
            "reason": "Called T+ voucher list route.",
            "dry_run": False,
            "request": result.get("request"),
            "data": result.get("data"),
            "route_result": result,
        }

    def _call_natural_template(
        self,
        parsed: dict[str, Any],
        *,
        dry_run: bool,
        body_overrides: Any,
        headers: dict[str, str] | None,
        query: dict[str, Any] | None,
        account_alias: str | None,
    ) -> dict[str, Any]:
        api_name = NATURAL_ACTION_API_NAMES.get(parsed["action"])
        search_result = self.search_api_templates(
            query=parsed["business_object"],
            product=parsed["product"],
            api_name=api_name,
            limit=5,
        )
        candidates = [
            self._natural_template_candidate(parsed, template)
            for template in search_result["templates"]
        ]
        candidates.sort(key=lambda item: item["score"], reverse=True)
        if not candidates:
            return self._natural_suggestion(
                parsed,
                confidence=self._natural_confidence(parsed, template_found=False),
                missing=["template"],
                reason="No official API template matched the natural request.",
            )
        if len(candidates) > 1 and candidates[0]["score"] - candidates[1]["score"] <= NATURAL_CLOSE_CANDIDATE_DELTA:
            return self._natural_suggestion(
                parsed,
                confidence=candidates[0]["score"],
                missing=["template_choice"],
                reason="Multiple official API templates matched the natural request.",
                candidates=candidates[:5],
            )
        selected = candidates[0]
        if selected["score"] < NATURAL_CALL_THRESHOLD:
            return self._natural_suggestion(
                parsed,
                confidence=selected["score"],
                missing=selected["missing"],
                reason="Natural route confidence is below call threshold.",
                candidates=candidates[:5],
            )
        if dry_run:
            return {
                "parsed_intent": parsed,
                "confidence": selected["score"],
                "decision": "call",
                "selected_tool": "call_api_smart",
                "candidates": [selected],
                "missing": [],
                "reason": "Dry run selected official API template route.",
                "dry_run": True,
                "request": selected["request"],
                "data": None,
            }
        module = selected["module"]
        result = self.call_api_smart(
            product=parsed["product"],
            parent_code=module["parent_code"],
            module_code=module["module_code"],
            api_name=api_name,
            fields=parsed["fields"],
            body_overrides=body_overrides,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )
        return {
            "parsed_intent": parsed,
            "confidence": selected["score"],
            "decision": "call",
            "selected_tool": "call_api_smart",
            "candidates": [selected],
            "missing": [],
            "reason": "Called official API template route.",
            "dry_run": False,
            "request": result.get("request"),
            "data": result.get("data"),
            "route_result": result,
        }

    def _natural_template_candidate(
        self,
        parsed: dict[str, Any],
        template: dict[str, Any],
    ) -> dict[str, Any]:
        module = template.get("module") or {}
        score = self._natural_confidence(
            parsed,
            template_found=True,
            field_confidence=bool(parsed.get("fields") or parsed.get("filters") or parsed.get("display_fields")),
        )
        return {
            "tool": "call_api_smart",
            "product": parsed["product"],
            "action": parsed["action"],
            "module": module,
            "api_name": template.get("api_name"),
            "path": template.get("path"),
            "score": score,
            "reason": "Official template matched business object and action.",
            "missing": [],
            "request": {
                "product": parsed["product"],
                "parent_code": module.get("parent_code"),
                "module_code": module.get("module_code"),
                "api_name": NATURAL_ACTION_API_NAMES.get(parsed["action"]),
                "fields": parsed.get("fields"),
            },
        }
```

- [ ] **Step 5: Run new tests to verify GREEN**

Run:

```bash
.venv/bin/python -m unittest \
  tests.test_client.ClientTests.test_safe_call_natural_wraps_empty_input \
  tests.test_client.ClientTests.test_call_natural_suggests_when_product_is_missing \
  tests.test_client.ClientTests.test_call_natural_routes_tplus_voucher_list_request \
  tests.test_client.ClientTests.test_call_natural_dry_run_returns_hyc_route_without_business_call \
  tests.test_client.ClientTests.test_call_natural_calls_hyc_create_when_single_template_matches \
  tests.test_client.ClientTests.test_call_natural_suggests_when_multiple_templates_match
```

Expected: all six tests pass.

- [ ] **Step 6: Run client suite**

Run:

```bash
.venv/bin/python -m unittest tests.test_client
```

Expected: all client tests pass.

- [ ] **Step 7: Commit client implementation**

Run:

```bash
git add src/chanjet_tcloud_mcp/client.py tests/test_client.py
git commit -m "feat: add natural API router"
```

## Task 3: MCP Tool Wrapper

**Files:**
- Modify: `src/chanjet_tcloud_mcp/server.py`

- [ ] **Step 1: Add server wrapper**

Insert this wrapper after `diagnose_config` and before `get_api_call_template`:

```python
@mcp.tool()
def call_natural(
    user_input: str,
    product: str | None = None,
    dry_run: bool = False,
    fields: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    page_size: int = 20,
    page_index: int = 1,
    headers: dict[str, str] | None = None,
    query: dict[str, Any] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Route a natural-language request to the safest matching Chanjet tool.

    This deterministic router parses product, action, business object, fields,
    filters, and display columns. It calls only high-confidence routes; otherwise
    it returns ranked candidates for the LLM/client to inspect.
    """
    return client.safe_call_natural(
        user_input=user_input,
        product=product,
        dry_run=dry_run,
        fields=fields,
        filters=filters,
        display_fields=display_fields,
        body_overrides=body_overrides,
        page_size=page_size,
        page_index=page_index,
        headers=headers,
        query=query,
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
git commit -m "feat: expose natural API router"
```

## Task 4: Documentation

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add README section**

Insert this section before the existing `call_api_smart` section:

````markdown
`call_natural`

面向 LLM 客户端的最高层入口。它接收自然语言请求，确定性解析产品、动作、业务对象、字段、查询条件和显示字段，再路由到现有 MCP 工具。它不是内置大模型；低置信度或多候选时不会猜测调用接口，而是返回候选和缺失信息。

适用示例：

```json
{
  "user_input": "查询所有生产加工单，显示单据编号和数量",
  "filters": {
    "单据编号": "MO-001"
  },
  "page_size": 50,
  "page_index": 1,
  "account_alias": "company-a"
}
```

```json
{
  "user_input": "好业财新增仓库，编码 WH001，名称 上海仓",
  "dry_run": true
}
```

返回结构：

```json
{
  "ok": true,
  "data": {
    "parsed_intent": {},
    "confidence": 0.85,
    "decision": "call",
    "selected_tool": "query_tplus_voucher_list_smart",
    "candidates": [],
    "request": {},
    "data": {}
  }
}
```

处理规则：

1. 高置信度才调用业务接口。
2. `dry_run=true` 时只返回将要调用的工具和请求草案。
3. 产品缺失、多产品可选、多模板接近或字段无法匹配时返回 `decision: "suggest"`，不会调用业务接口。
4. T+ 单据列表请求会路由到 `query_tplus_voucher_list_smart`。
5. 其他产品的明确单模板请求会路由到 `call_api_smart`。
````

- [ ] **Step 2: Verify README fences**

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

- [ ] **Step 3: Commit docs**

Run:

```bash
git add README.md
git commit -m "docs: document natural API router"
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

Report the commit range and verification commands. Mention that `call_natural` is deterministic, routes T+ list requests to `query_tplus_voucher_list_smart`, routes single-template product calls to `call_api_smart`, supports `dry_run`, and returns `decision="suggest"` instead of guessing when confidence is low.
