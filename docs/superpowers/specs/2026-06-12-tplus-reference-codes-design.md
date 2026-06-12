# T+ Reference Codes Design

## Goal

Add a public MCP tool that lets clients look up T+ document type `bizCode` values and business type `BusinessType` values before calling voucher/list APIs.

## Tool

Expose one tool named `get_tplus_reference_codes`.

Inputs:

- `query`: optional string. When omitted, return both full reference tables. When present, return only rows whose code, name, or raw official-doc content matches the query.

Output:

```json
{
  "ok": true,
  "data": {
    "voucher_types": [{"code": "SA04", "name": "销货单", "raw": {}}],
    "business_types": [{"code": "02", "name": "采购退货", "raw": {}}],
    "source_docs": {
      "voucher_types": {"product": "tcloud", "parent_code": "t+xdescription", "module_code": "t+vouchertype"},
      "business_types": {"product": "tcloud", "parent_code": "t+xdescription", "module_code": "t+busitype"}
    }
  }
}
```

The tool uses the existing `{ok, data/error}` envelope pattern used by diagnostics and template tools.

## Data Flow

The client fetches two fixed official T+ document details through the existing document API:

- `get_doc("tcloud", "t+xdescription", "t+vouchertype")`
- `get_doc("tcloud", "t+xdescription", "t+busitype")`

It then walks the returned document payload defensively and extracts list rows containing likely code/name fields. The extractor preserves each source row as `raw` because official document payload shape can vary.

## Matching

The optional `query` is normalized the same way existing display-field matching works: lowercased and stripped to alphanumeric characters. A row matches when the query appears in its normalized code, name, or raw source content.

## Documentation

The README should tell users to call `get_tplus_reference_codes` when they do not know a T+ `bizCode` or `BusinessType`.
