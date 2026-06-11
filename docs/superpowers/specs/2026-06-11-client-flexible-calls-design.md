# MCP Client Flexible Calls Design

## Goal

Make the MCP server easier for clients to use after they configure core Chanjet credentials. The server should clearly report whether the current configuration can call documentation tools, OAuth tools, and business APIs; help clients convert official documentation entries into callable payload templates; and return predictable error envelopes for common failures.

## Scope

This change focuses on client-facing additions:

- `diagnose_config`: safe configuration and account readiness diagnostics.
- `get_api_call_template`: product-specific API call template extraction from official docs.
- `search_api_templates`: keyword search that returns callable templates directly.
- `call_api_template`: template-driven product routing and API invocation.
- Standardized MCP tool error envelopes for diagnostics and template/call wrappers.

The existing `call_tplus_api`, `call_hyc_api`, `call_hsy_api`, `call_ydz_api`, `call_hkj_api`, OAuth tools, and document lookup tools remain available and keep their current signatures.

## MCP Tools

### `diagnose_config`

Returns a safe summary with no secrets:

- `settings`: whether `app_key`, `app_secret`, `redirect_uri`, and token store path are present.
- `accounts`: active account alias, stored account count, active account token presence, and expiration status.
- `capabilities`: booleans for documentation lookup, OAuth URL generation, token exchange, and authenticated business API calls.
- `issues`: machine-readable issue objects with `code`, `message`, and `hint`.

The tool must not perform network requests. It only inspects environment-derived settings and the local token store.

### `get_api_call_template`

Accepts:

- `product`: one of `tcloud`, `tplus`, `hyc`, `zplus`, `hsy`, `haoshengyi`, `ydz`, `finance`, `hkj`, `accounting`.
- `parent_code`
- `module_code`
- optional `api_name` filter.

The tool reads the official document detail for the selected product, extracts API entries, and returns templates containing:

- product and module metadata.
- API display name if available.
- `path`, `method`, `body`, `query`, and `headers` placeholders where discoverable.
- `tool`: the recommended MCP call tool, such as `call_tplus_api`.
- `arguments`: a ready-to-edit MCP argument object.

Extraction must be defensive because official document payloads can vary. If exact method or payload examples are missing, use `POST` and empty placeholders.

### `search_api_templates`

Accepts a business keyword, optional product, optional API name filter, and limit. It searches the relevant official module tree, loads matching module details, and returns enriched templates that include product metadata, module metadata, the recommended tool, and ready-to-edit arguments.

If product is omitted, the server searches all supported products in a deterministic order.

### `call_api_template`

Accepts product, parent code, module code, optional API name filter, and request overrides (`body`, `query`, `headers`, `account_alias`, `method`). It loads the matching official template, merges caller overrides, and routes to the correct low-level product call method.

The response includes the selected template, final request arguments, and raw business API response.

### Error Envelope

New safe wrappers should use a consistent object:

```json
{
  "ok": false,
  "error": {
    "code": "missing_config",
    "message": "Missing required Chanjet settings: CHANJET_APP_KEY",
    "hint": "Set CHANJET_APP_KEY in the MCP client env or .env file.",
    "trace_id": null
  }
}
```

Successful diagnostic/template wrapper responses use `ok: true` with `data`.

The existing low-level call tools may continue returning raw API responses to avoid breaking callers. The new wrappers should normalize local validation errors and transport errors.

## Data Flow

`server.py` exposes thin MCP wrappers. `ChanjetTCloudClient` owns product normalization, configuration diagnostics, doc extraction, and error envelope helpers. Existing transport and token store abstractions remain unchanged.

## Error Handling

Configuration and account errors become structured `issues` in `diagnose_config`. Template extraction failures become error envelopes with actionable hints. Missing official fields should not fail template generation; templates should include conservative defaults instead.

## Testing

Unit tests should cover:

- Diagnostics with missing credentials and no account.
- Diagnostics with active stored account.
- Product alias normalization for template generation.
- Template extraction from a representative document payload.
- Keyword template search over official module docs.
- Template-driven product routing for API calls.
- Error envelope conversion for validation failures.
