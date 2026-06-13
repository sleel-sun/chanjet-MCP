# All-Product Smart API Call Design

## Goal

Add one smart API calling path for all supported Chanjet products: T+Cloud, HYC/ZPlus, HSY, YDZ/Finance, and HKJ/Accounting.

The smart caller must always start from the official API document template. It must also translate user-provided Chinese field names into the actual API request field names before sending the request. If a requested Chinese field cannot be resolved, the tool must return a structured error instead of sending an incomplete or incorrect API request.

## Tool Shape

Expose a new MCP tool named `call_api_smart`.

Inputs:

- `product`: one of `tplus`, `tcloud`, `hyc`, `zplus`, `hsy`, `haoshengyi`, `ydz`, `finance`, `hkj`, or `accounting`.
- `parent_code`, `module_code`, `api_name`: identify the official API document entry.
- `fields`: optional dictionary of user-facing field names to values. Keys may be Chinese labels from the official documentation.
- `body_overrides`: optional explicit request body overrides, applied after field resolution.
- `query`, `headers`, `account_alias`, `method`: normal call settings.
- T+ only: `voucher_name`, `biz_code`, `business_type_name`, `business_type`, `filters`, and `display_fields`.

Keep `call_tplus_api_smart` as a compatibility wrapper. It should call the same shared smart-call implementation with `product="tplus"` so T+ behavior stays consistent.

## Field Resolution

The smart caller must resolve user-facing Chinese fields before calling the business API.

Resolution sources, in priority order:

1. Product-specific helper metadata when available.
2. Field metadata extracted from the official API document entry.
3. The official request example keys as exact field-name fallbacks.

For T+ voucher list calls, product-specific metadata is already available through `get_tplus_voucher_list_fields`. Use it for `filters` and `display_fields`, and keep the existing `voucher_name` to `biz_code` and `business_type_name` to `BusinessType` resolution.

For HYC, HSY, YDZ, and HKJ, use the official API document entry to build a field alias map. The mapper should recognize common field metadata keys such as field name/code, parameter name, label, caption, title, description, and Chinese name when present in the document payload. It should also recursively inspect nested parameter structures because official documents may place request fields in arrays or nested objects.

If the official document does not expose enough metadata for a Chinese field, the smart caller must return an `invalid_argument` error that lists the unresolved fields and includes a hint to use exact API field names or inspect the API template first.

## Request Construction

The smart caller should:

1. Fetch `get_api_call_template(product, parent_code, module_code, api_name)`.
2. Select the first matched official template.
3. Copy the template `arguments` as the base request.
4. Resolve `fields` into actual request body fields and merge them into the body.
5. Apply T+ special handling when `product` resolves to T+Cloud.
6. Deep-merge `body_overrides` last so explicit user overrides remain authoritative.
7. Apply `method`, `query`, `headers`, and `account_alias` overrides.
8. Route the final request through `_call_api_by_product`.

Field injection should preserve the existing request body shape. If the template body contains a top-level `param` object, resolved fields should default into `body.param`; otherwise they should default into the top-level body object. Explicit nested field paths from metadata should be respected when available.

## Output

Successful responses return:

- `template`: the official request template used.
- `resolved`: product code, matched body fields, unresolved field list, and T+ code/field metadata when applicable.
- `request`: final request sent to the business API.
- `data`: raw API response.

Errors use the existing unified tool error envelope:

```json
{
  "ok": false,
  "error": {
    "code": "invalid_argument",
    "message": "Unmatched smart fields: 客户名称",
    "hint": "Use exact API field names or call get_api_call_template/search_api_templates to inspect available fields.",
    "trace_id": null
  }
}
```

## Compatibility

Existing tools remain available:

- `call_api_template` remains the explicit template-based caller. It should not change semantics.
- `call_tplus_api_smart` remains available for existing T+ clients and delegates to the shared smart-call implementation.
- Low-level `call_tplus_api`, `call_hyc_api`, `call_hsy_api`, `call_ydz_api`, and `call_hkj_api` remain available for fully manual calls.

## Testing

Add tests before implementation:

- `call_api_smart` fetches an HYC/HKJ-style official template, resolves Chinese `fields` into API body field names, and routes through the correct product call.
- `call_api_smart` returns a structured error when a Chinese field cannot be resolved.
- `call_api_smart` supports exact API field names as a fallback.
- `call_api_smart` preserves T+ smart behavior by resolving voucher names, business type names, filters, and display fields.
- `call_tplus_api_smart` delegates to the shared behavior and remains backward compatible.

Full verification remains:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
.venv/bin/python -c "from chanjet_tcloud_mcp.server import mcp; print(mcp.name)"
git diff --check
```
