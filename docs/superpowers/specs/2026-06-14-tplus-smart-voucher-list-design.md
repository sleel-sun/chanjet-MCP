# T+ Smart Voucher List Query Design

## Goal

Add one high-level MCP tool for natural T+ voucher list queries without hardcoding every voucher API path. The tool should handle requests such as "query all production processing orders" by resolving the voucher, locating the official list-query API template, generating a valid request body, and calling the business API.

The new behavior must be generic. It may keep small compatibility maps for stable voucher codes and known bad module-code aliases, but it must not maintain a per-voucher table of `parent_code`, `module_code`, `api_name`, and `path`.

## Public Tool

Expose `query_tplus_voucher_list_smart` in `server.py`.

Inputs:

- `voucher_name`: required natural voucher name, for example `生产加工单`.
- `intent`: optional natural intent. Defaults to list query. Values containing `列表`, `查询`, `所有`, or `全部` are treated as list-query intent.
- `filters`: optional dict of natural query fields and values.
- `display_fields`: optional list of natural display column names.
- `page_size`: optional integer, default `20`.
- `page_index`: optional integer, default `1`.
- `body_overrides`: optional dict merged last into the generated request body.
- `parent_code`, `module_code`, `api_name`, `path`, `method`, `query`, `headers`, `account_alias`: optional explicit hints for compatibility and advanced callers.

Outputs:

- `data`: raw business API response.
- `template`: selected official API template.
- `request`: final path, method, query, headers, account alias, and body sent to Chanjet.
- `resolved`: voucher code, selected document module, selected template reason, matched fields, and compatibility decisions.

Safe wrapper errors use the existing `tool_error` envelope.

## Resolution Flow

1. Normalize intent. If intent is empty or contains a list marker, use list-query mode. Non-list intents raise `ValueError` with a hint to use `call_api_smart` for other operations.
2. Resolve `biz_code`.
   - First call `get_tplus_reference_codes(query=voucher_name)` and use `_resolve_reference_code` semantics.
   - If no official reference row matches, use a small voucher-code fallback map for stable missing rows. Initial entry: `生产加工单 -> MP05`.
   - Record whether the code came from official docs or fallback.
3. Resolve the official list template.
   - If `path` is supplied, treat it as an advanced explicit request-path override. Still search official docs best-effort for template metadata, but do not fail only because the explicit path has no matching document entry.
   - Otherwise search official docs with query variants derived from `voucher_name` and list intent, such as `生产加工单 列表查询`, `生产加工单 查询`, and `生产加工单`.
   - Prefer templates whose `api_name` or path contains `FindVoucherList`.
   - Then prefer templates whose API name contains list-query markers.
   - Then prefer templates from modules whose name or path contains the voucher name.
   - If explicit `parent_code`, `module_code`, or `api_name` are valid, they can narrow selection. If they do not resolve and `voucher_name` is present, continue with search instead of failing immediately.
4. Apply compatibility mapping for bad module-code input.
   - Treat values such as `ManufactureOrderOpenApi` as implementation/API-class aliases, not official document module codes.
   - If `voucher_name` is present, ignore the bad module code and continue document search. Record this in `resolved.compatibility`.
   - If `voucher_name` is absent, return a standard invalid-argument error instructing the caller to pass `voucher_name`.
5. Generate the request body.
   - Start from the selected official template body when it is an object. If missing or unusable, start from `{}`.
   - Ensure `body.param` exists as an object.
   - Ensure `body.param.pageSize` and `body.param.pageIndex` exist from `page_size` and `page_index`, unless already set by the template. `body_overrides` may still replace them during the final merge.
   - Ensure `body.param.paramDic` exists as an object.
   - Resolve `filters` through `get_tplus_voucher_list_fields` using the resolved voucher `biz_code`. Matched filter values are written into `body.param.paramDic`.
   - Resolve `display_fields` through display columns. Matched fields are written into `body.param.selectFields`, unless an existing field-selection key is already present.
   - Deep merge `body_overrides` last.
6. Call the T+ API through the existing authenticated `call_tplus_api` path.

## Generic Boundaries

The implementation should add generic helpers instead of voucher-specific methods:

- `_is_tplus_list_intent(intent)`
- `_tplus_voucher_search_queries(voucher_name, intent)`
- `_resolve_tplus_voucher_biz_code(voucher_name)`
- `_find_tplus_voucher_list_template(voucher_name, intent, hints)`
- `_rank_tplus_voucher_list_template(candidate, voucher_name)`
- `_tplus_list_body(body)`
- `_inject_tplus_list_filters(body, filters, query_fields)`
- `_normalize_tplus_module_hint(module_code)`

Allowed static data:

- `TPLUS_VOUCHER_BIZ_CODE_FALLBACKS`, only for stable code gaps not discoverable from official docs.
- `TPLUS_MODULE_CODE_ALIASES`, only for known invalid caller inputs such as `ManufactureOrderOpenApi`.

Not allowed:

- A table that maps every voucher to fixed `parent_code`, `module_code`, `api_name`, or `path`.
- Special-case branches for one voucher's list API.
- Silent calls when template selection or field matching is ambiguous.

## Error Handling

Return `invalid_argument` for user-fixable problems:

- unsupported non-list intent;
- missing `voucher_name` when no reliable template hints are available;
- ambiguous or missing voucher code;
- no official list-query template found;
- unmatched filter or display fields.

When a caller passes a bad `module_code` but also passes `voucher_name`, the tool should not fail on the bad module code. It should record a compatibility decision and continue with search.

## Tests

Add tests before implementation:

- `query_tplus_voucher_list_smart` resolves `生产加工单` to fallback `MP05` when official references do not include it.
- It searches official docs with voucher-name plus list-query terms and selects a `FindVoucherList` template.
- It generates `pageSize`, `pageIndex`, `paramDic`, and `selectFields`.
- It maps natural filter fields into `param.paramDic`.
- It tolerates `module_code="ManufactureOrderOpenApi"` when `voucher_name="生产加工单"` is present.
- It returns a standard error and does not call the business API when no list template is found.
- Existing `call_api_smart`, `call_tplus_api_smart`, and `query_tplus_voucher_list` tests continue to pass.

## Documentation

Update README guidance so clients prefer `query_tplus_voucher_list_smart` for natural list requests such as "查生产加工单列表" or "查询所有销货单". Keep `call_api_smart` documented as the lower-level API-template caller for non-list operations and advanced explicit calls.
