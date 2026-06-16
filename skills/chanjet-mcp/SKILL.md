---
name: chanjet-mcp
description: Use when handling Changjie/Chanjet/畅捷通 business API requests through any configured Chanjet MCP server, including T+Cloud/T+, 好业财/HYC/ZPlus, 好生意/HSY, 易代账/YDZ/Finance, or 好会计/HKJ/Accounting queries, creates, updates, voucher lists, field mapping, bizCode, BusinessType, account_alias, or Chinese label-to-code issues.
---

# Chanjet MCP

## Overview

Use the configured Chanjet MCP tools as the execution layer. This skill provides a generic calling strategy so agents pick the safest tool, pass Chinese business labels correctly, and avoid guessing product/module/API details.

## Availability Check

- If Chanjet MCP tools are visible, use them directly.
- If no Chanjet MCP tools are available, state that the Chanjet MCP server is not configured in this environment and ask the user to install or connect it.
- If configuration, account, token, or `account_alias` status is uncertain, call `diagnose_config` before business API calls.
- Do not assume a local repository path, virtualenv path, token file path, or company account alias unless the user or tool output provides it.

## Default Flow

1. For user business requests in natural language, call `call_natural` first.
2. If `call_natural` returns `decision: "call"`, use its result; do not second-guess the selected tool.
3. If it returns `decision: "suggest"`, inspect `missing`, `reason`, and `candidates`; ask for the missing product, business object, action, or template choice instead of forcing a call.
4. For structured calls where product/module/API are known, use `call_api_smart`.
5. Use `call_api_template` or raw product tools only when the caller needs exact low-level control.

## Tool Selection

| Need | Prefer |
| --- | --- |
| Natural request like "查询生产加工单显示单据编号" | `call_natural` |
| Known product/module/API plus Chinese fields | `call_api_smart` |
| T+ voucher list by voucher name | `query_tplus_voucher_list_smart` |
| Known T+ document list `biz_code` and path | `query_tplus_voucher_list` |
| Need reference codes for T+ voucher/business type | `get_tplus_reference_codes` |
| Need T+ list query/display field names | `get_tplus_voucher_list_fields` |
| Need discoverable official API templates | `search_api_templates` |
| Need exact product path call | `call_tplus_api`, `call_hyc_api`, `call_hsy_api`, `call_ydz_api`, `call_hkj_api` |

## Field Rules

- Pass Chinese field labels directly when using smart/template/raw calls; the MCP maps labels to real field codes when official template metadata is available.
- For `call_api_smart`, use `fields` for request values such as `{"编码": "WH001", "名称": "上海仓"}`.
- For query/list filtering, use `filters` with Chinese labels when available.
- For selected response columns, use `display_fields`, for example `["单据编号", "客户", "金额"]`.
- For raw product calls, Chinese keys in `body` or `query` are converted only when the MCP can match `path` to an official template. Already using real field codes avoids extra template lookup.
- Do not invent field codes when mapping fails. Use `get_api_call_template`, `search_api_templates`, or field lookup tools to inspect available fields.
- If the MCP implementation does not support automatic label mapping on raw calls, fall back to `call_api_smart` or inspect templates before calling.

## Template Matching

- Basic archives and document templates may be described as parent + object phrases such as `基础档案仓库`, `基础档案客户`, or `单据模板销货单`.
- Do not stop after matching only a parent module such as `基础档案`; continue through `call_natural` or `search_api_templates` until a callable child template is selected.
- Once the child template is selected, pass Chinese labels normally through `fields`, `filters`, and `display_fields`; the MCP handles label-to-code conversion when template metadata is available.

## T+ Specifics

- `voucher_name` is the human document name, such as `销货单` or `生产加工单`.
- `biz_code` is the official T+ document code, such as `SA04` or `MP05`.
- `business_type_name` is the human business type name; `business_type` is the official code, such as `02`.
- If `bizCode` or `BusinessType` is needed and unknown, call `get_tplus_reference_codes`.
- For T+ voucher list filters and columns, prefer `query_tplus_voucher_list_smart`; it resolves `biz_code`, finds a list template, injects `paramDic`, and writes `selectFields`.

## Examples

Natural voucher list:

```json
{
  "user_input": "查询所有生产加工单，显示单据编号和数量",
  "filters": {"单据编号": "MO-001"},
  "page_size": 50,
  "account_alias": "company-a"
}
```

Structured smart create:

```json
{
  "product": "hyc",
  "parent_code": "zjjcda",
  "module_code": "ck",
  "api_name": "新增",
  "fields": {"编码": "WH001", "名称": "上海仓"},
  "account_alias": "company-a"
}
```

T+ smart query with display fields:

```json
{
  "parent_code": "t+jcda",
  "module_code": "t+ck",
  "api_name": "查询",
  "filters": {"编码": "WH001"},
  "display_fields": ["编码", "名称"],
  "account_alias": "company-a"
}
```

## Common Mistakes

- Do not call raw product tools first for ordinary user requests; use `call_natural` or `call_api_smart`.
- Do not treat every T+ list request as a voucher list. Basic archives such as warehouse/customer inventory can route through `call_api_smart`.
- Do not continue after `decision: "suggest"` unless the missing information is obvious from user context.
- Do not manually translate Chinese labels to guessed English codes; let the MCP template mapper do it.
- Do not omit `account_alias` when the user clearly wants a specific company/account.
- Do not claim an API call was made if the MCP server or account configuration is missing.
