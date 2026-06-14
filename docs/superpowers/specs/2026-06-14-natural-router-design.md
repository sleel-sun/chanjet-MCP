# Natural API Router Design

## Goal

Add a unified MCP tool that accepts natural user text and routes it to existing Chanjet tools across T+Cloud, HYC/ZPlus, HSY, YDZ/Finance, and HKJ/Accounting.

The router should improve client consistency when an LLM calls the MCP server, but the MCP server should not embed an LLM. It should use deterministic parsing, official document search, candidate ranking, and confidence scoring.

## Public Tool

Expose `call_natural` in `server.py`.

Inputs:

- `user_input`: required natural-language request.
- `product`: optional product hint.
- `dry_run`: optional bool, default `False`. When true, never call a business API.
- `fields`: optional explicit field values for create/update style requests.
- `filters`: optional explicit filter values for list/query requests.
- `display_fields`: optional display columns for list/query requests.
- `body_overrides`: optional explicit request body overrides.
- `page_size`: optional list page size, default `20`.
- `page_index`: optional list page index, default `1`.
- `headers`, `query`, `account_alias`: optional pass-through call settings.

Output shape:

- `parsed_intent`: product, action, business object, voucher name, filters, display fields, explicit fields, and unresolved text.
- `confidence`: numeric score from 0 to 1.
- `decision`: `call`, `suggest`, or `error`.
- `selected_tool`: tool that would be called or was called.
- `candidates`: ranked candidate tools/templates with reasons.
- `request`: final request or request draft when available.
- `data`: business API response when a call is actually made.

## Parsing Scope

Product aliases:

- T+Cloud: `tplus`, `tcloud`, `T+`, `T+Cloud`
- HYC/ZPlus: `hyc`, `zplus`, `好业财`
- HSY: `hsy`, `haoshengyi`, `好生意`
- YDZ/Finance: `ydz`, `finance`, `易代账`
- HKJ/Accounting: `hkj`, `accounting`, `好会计`

Action aliases:

- List/query: `列表`, `查询`, `查`, `所有`, `全部`, `list`, `query`, `all`
- Create/add: `新增`, `创建`, `添加`, `保存`, `create`, `add`, `save`
- Update/edit: `修改`, `更新`, `编辑`, `update`, `edit`
- Delete/remove: `删除`, `移除`, `作废`, `delete`, `remove`
- Audit/approve: `审核`, `审批`, `通过`, `audit`, `approve`
- Unaudit/unapprove: `弃审`, `反审核`, `取消审核`, `unaudit`, `unapprove`

The first implementation should parse simple Chinese and English keyword patterns only. It should not attempt broad NLP, entity extraction from arbitrary grammar, or multi-step planning.

## Routing Rules

1. Parse `user_input` into a `parsed_intent`.
2. If `product` is provided, prefer it over parsed product aliases.
3. If product is missing or multiple products are plausible, return `decision="suggest"` with candidates and do not call. Exception: a T+ voucher-list request may default to `tplus` only when the business object resolves through `get_tplus_reference_codes` or `TPLUS_VOUCHER_BIZ_CODE_FALLBACKS`.
4. If the request is a T+ voucher list/query intent and a voucher/business object is identified, route to `query_tplus_voucher_list_smart`.
5. If product, business object/module, and action are identified for a non-list or non-T+ request, search official docs through `search_api_templates` and rank templates by product, module name/path, API name, path, and action markers.
6. If exactly one candidate clears the confidence threshold, route to `call_api_smart`.
7. If no candidate or multiple close candidates exist, return `decision="suggest"` with up to 5 ranked candidates and no business API call.
8. If `dry_run=True`, return the selected route and request draft without calling business APIs even when confidence is high.

## Confidence Model

Use deterministic scoring. Suggested first-pass weights:

- Product identified explicitly: +0.25
- Action identified: +0.20
- Business object or voucher name identified: +0.20
- Official template match found: +0.25
- Field/filter/display-field match confidence: +0.10

Call threshold: `0.75`.

Suggest threshold: any score below `0.75`, multiple candidates within `0.10`, or missing required call parameters.

The router must not guess-call when confidence is low.

## Candidate Output

Each candidate should include:

- `tool`: `query_tplus_voucher_list_smart`, `call_api_smart`, or `search_api_templates`.
- `product`.
- `action`.
- `module`: parent/module codes and display names when known.
- `api_name`.
- `path`.
- `score`.
- `reason`.
- `missing`: required fields or hints still needed before calling.

## Data Flow

### T+ Voucher List Query

Example input: `查询所有生产加工单，显示单据编号和数量`.

Expected parsing:

- product: `tplus` by default because `生产加工单` resolves through the T+ voucher fallback table.
- action: `list`
- voucher_name: `生产加工单`
- display_fields: `["单据编号", "数量"]`

Route:

- `call_natural` calls `query_tplus_voucher_list_smart`.
- The existing smart list tool resolves `MP05`, searches `FindVoucherList`, builds `paramDic/selectFields`, and calls T+.

### Generic Product Template Call

Example input: `好业财新增仓库，编码 WH001，名称 上海仓`.

Expected parsing:

- product: `hyc`
- action: `create`
- business object: `仓库`
- fields: `{"编码": "WH001", "名称": "上海仓"}`

Route:

- Search official docs for `仓库` in `hyc` with action marker `新增`.
- If one template matches, call `call_api_smart`.
- If multiple templates match, return suggestions without calling.

## Error and Suggestion Behavior

Return a safe envelope using existing `tool_success` or `tool_error` conventions.

Low confidence is not a transport or API error. Prefer a success envelope with `decision="suggest"` so LLM clients can inspect candidates and ask follow-up questions.

Use invalid-argument error only for structurally invalid input, such as empty `user_input`.

## Non-Goals

- No embedded LLM calls in the MCP server.
- No guessing destructive actions.
- No automatic multi-step workflows.
- No broad grammar parser.
- No per-voucher or per-module hardcoded full route table.

## Tests

Add tests before implementation:

- Empty `user_input` returns invalid-argument envelope.
- `查询所有生产加工单，显示单据编号和数量` routes to `query_tplus_voucher_list_smart`.
- Low-confidence ambiguous product input returns `decision="suggest"` and does not call a business API.
- `dry_run=True` returns selected route/request draft and does not call business API.
- `好业财新增仓库，编码 WH001，名称 上海仓` searches HYC templates and calls `call_api_smart` when one candidate matches.
- Multiple matching templates return top candidates and no call.
- Existing direct smart tools continue to pass.

## Documentation

Update README to describe `call_natural` as the highest-level entry point for LLM clients. Document that it is a deterministic router, not a full language model, and that low-confidence cases return candidates instead of guessing.
