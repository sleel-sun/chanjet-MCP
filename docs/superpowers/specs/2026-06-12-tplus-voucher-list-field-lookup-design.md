# T+ Voucher List Field Lookup Design

## Goal

Add a lookup path for T+ voucher list query fields and display columns. When an MCP client does not know which query parameter fields or display column fields are valid for a T+ document list query, it should call the lookup tool before querying list data.

## Source Reference

The official source page is:

- `tcloud/t+dj/djlbcxfz`
- URL: `https://open.chanjet.com/docs/file/apiFile/tcloud/t%2Bdj/djlbcxfz`

That page documents the helper APIs for list query fields and display columns:

- `POST /tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode`
- `POST /tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`

## Tool

Expose `get_tplus_voucher_list_fields`.

Inputs:

- `biz_code`: required T+ document type code, such as `SA04`.
- `query`: optional filter. It matches field identifiers, labels, and raw source values.
- `headers`, `account_alias`: same account-selection behavior as other T+ calls.

Output:

```json
{
  "ok": true,
  "data": {
    "biz_code": "SA04",
    "query_fields": [{"field": "Code", "label": "单据编号", "raw": {}}],
    "display_fields": [{"field": "CustomerName", "label": "客户", "raw": {}}],
    "source_doc": {
      "product": "tcloud",
      "parent_code": "t+dj",
      "module_code": "djlbcxfz"
    }
  }
}
```

## Voucher List Query Behavior

`query_tplus_voucher_list` should use the same helper source. Before calling the actual list path, it loads both query fields and display columns for `biz_code`.

The tool still only injects display field selection into `body.param.selectFields`, because query field values must come from the caller's business intent. The response includes `query_fields` so the caller can inspect valid query parameters when building `body.param`.

## Documentation

README and MCP tool descriptions should state:

- Unknown `biz_code`: call `get_tplus_reference_codes`.
- Unknown query fields or display columns for list queries: call `get_tplus_voucher_list_fields`.
- Query conditions belong in `body.param`.
- Requested display columns can be passed as `display_fields`.
