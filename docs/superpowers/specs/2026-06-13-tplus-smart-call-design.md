# T+ Smart API Call Design

## Goal

Add a higher-level T+ call tool that always starts from the official API request example before calling the business API, then resolves common natural-language inputs for voucher codes, business types, query fields, and display columns.

## Tool

Expose `call_tplus_api_smart`.

Inputs:

- `parent_code`, `module_code`, `api_name`: identify the official T+ API documentation entry.
- `voucher_name`: optional natural-language voucher type, such as `销货单`.
- `biz_code`: optional explicit voucher type code. If omitted and `voucher_name` is present, resolve it through `get_tplus_reference_codes`.
- `business_type_name`: optional natural-language business type, such as `采购退货`.
- `business_type`: optional explicit business type code. If omitted and `business_type_name` is present, resolve it through `get_tplus_reference_codes`.
- `filters`: optional dictionary of natural-language query field labels to values.
- `display_fields`: optional list of natural-language display column labels.
- `body_overrides`, `query`, `headers`, `account_alias`, `method`: explicit overrides and normal call settings.

## Behavior

The tool must call `get_api_call_template(product="tplus", ...)` first and use the first matched official request example as the base request. It should not build a request from scratch.

Resolution rules:

- `voucher_name` resolves to a `voucher_types.code`.
- `business_type_name` resolves to a `business_types.code`.
- If `biz_code` is available, load `get_tplus_voucher_list_fields` and use `query_fields` to map `filters` keys into `body.param`.
- If `display_fields` are supplied, map them through `display_fields` from `get_tplus_voucher_list_fields` and inject matched field identifiers into `body.param.selectFields`, unless a field-selection key already exists.
- `business_type` injects into `body.param.BusinessType`.
- `body_overrides` applies last as a deep merge.

If any requested filter or display field cannot be matched, return a structured error envelope in the safe wrapper instead of silently calling with incomplete intent.

## Output

Successful responses return:

- `template`: the official request example/template used.
- `resolved`: resolved `biz_code`, `business_type`, matched fields, and any lookup metadata.
- `request`: final request sent to T+.
- `data`: raw API response.

## Documentation

README and tool descriptions should tell MCP clients to use this tool for automatic T+ calls when they have natural-language field names, but still provide `parent_code`, `module_code`, and `api_name` so the tool can fetch the correct official request example.
