# T+ Voucher List Display Fields Design

## Goal

Add a dedicated MCP tool for T+ voucher list queries that preloads the available list display columns for the requested voucher type and automatically maps user-requested display field names to the API's actual column identifiers.

## Official Interfaces

Chanjet's AI documentation index points dynamic documentation pages to `/md` text endpoints. The relevant official T+ helper APIs are:

- `POST /tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`: 查询单据列表栏目项.
- `POST /tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode`: 查询单据列表查询项.

This feature uses `GetColumnSetByBizCode` before the actual list query because the requested enhancement is about display fields.

## MCP Tool

Expose `query_tplus_voucher_list` with these inputs:

- `biz_code`: T+ voucher business code, for example `SA03`.
- `path`: actual voucher list query API path.
- `method`: HTTP method, default `POST`.
- `body`: original list query request body.
- `display_fields`: optional field names requested by the MCP caller.
- `query`, `headers`, `account_alias`: same semantics as `call_tplus_api`.

## Behavior

The tool first calls `GetColumnSetByBizCode` with:

```json
{
  "bizCode": "SA03",
  "apiParam": {
    "dataSource": "openapi"
  }
}
```

It extracts columns from common response envelopes and nested structures. Each column is normalized into `field`, `name`, `title`, `caption`, `code`, `key`, and `raw` where available.

If `display_fields` is provided, the tool matches each requested value against column identifiers and labels using exact normalized matching first and then substring matching. Matched field identifiers are injected into the list query body under `param.selectFields` unless the caller already supplied `selectFields`, `fields`, `columns`, or `select`.

The result returns:

- `data`: the actual voucher list API response.
- `display_fields`: all normalized display columns discovered for the voucher type.
- `matched_display_fields`: matches for requested display fields.
- `unmatched_display_fields`: requested display fields that could not be mapped.

## Error Handling

Missing `biz_code` or `path` raises `ValueError`. The API calls reuse the existing T+ authorization, token refresh, and arbitrary API call handling in `ChanjetTCloudClient.call_tplus_api`.

## Testing

Client tests cover call ordering, helper payload, field matching, body injection, existing field-selection preservation, and direct MCP wrapper delegation.
