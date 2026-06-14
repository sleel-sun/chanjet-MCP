# Chanjet MCP Server

独立 Python MCP 服务，用于把畅捷通 T+Cloud、好业财（HYC/ZPlus）、好生意（HSY）、易代账（YDZ/Finance）和好会计（HKJ/Accounting）OpenAPI 文档与业务接口暴露给 MCP 客户端。

## 功能

- 查询 T+Cloud 官方 API 文档模块树。
- 查询好业财 HYC/ZPlus 官方 API 文档模块树。
- 查询好生意 HSY 官方 API 文档模块树。
- 查询易代账 YDZ/Finance 官方 API 文档模块树。
- 查询好会计 HKJ/Accounting 官方 API 文档模块树。
- 按模块编码读取官方接口详情。
- 按关键词搜索 T+Cloud、HYC/ZPlus、HSY、YDZ/Finance 或 HKJ/Accounting 文档模块。
- 诊断 MCP 客户端配置是否具备文档查询、OAuth 和业务接口调用能力。
- 从官方接口文档生成可直接编辑的 MCP 调用模板。
- 查询 T+ 单据类型 `bizCode` 和业务类型 `BusinessType` 对照表。
- 查询 T+ 单据列表查询项字段和显示栏目字段。
- 调用 T+ 接口前自动参考官方请求示例，并解析常见自然语言字段。
- 通用调用任意 `/tplus/api/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 HYC/ZPlus `/accounting/openapi/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 HSY OpenAPI 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 YDZ/Finance `/accounting/document/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 HKJ/Accounting `/accounting/document/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 生成 OAuth 授权链接、授权码换 token、刷新 token。
- 支持多账号 OAuth 授权管理，按账号别名保存 token，并在调用业务接口时自动刷新过期 token。

## 安装

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e .
```

## 配置

复制 `.env.example` 为 `.env`，填写畅捷通开放平台配置：

```bash
cp .env.example .env
```

关键变量：

```dotenv
CHANJET_APP_KEY=your_app_key
CHANJET_APP_SECRET=your_app_secret
CHANJET_ACTIVE_ACCOUNT=company-a
CHANJET_TOKEN_STORE_PATH=.chanjet_tokens.json
CHANJET_REDIRECT_URI=https://example.com/oauth/callback
```

`CHANJET_APP_KEY` 和 `CHANJET_APP_SECRET` 是应用级凭据。账号级 `openToken` / `refreshToken` 推荐通过 OAuth setup 自动写入本地 `.chanjet_tokens.json`，该文件已加入 `.gitignore`。

兼容旧用法：仍可在 `.env` 中配置 `CHANJET_OPEN_TOKEN` 和 `CHANJET_REFRESH_TOKEN` 作为单账号 fallback。如果只使用文档查询工具，可以暂时不配置业务接口凭据。

## 首次 OAuth 授权

`redirect_uri` 可以在每次调用工具时显式传入，也可以通过 `CHANJET_REDIRECT_URI` 设置默认值。显式参数优先于环境变量。

1. 调用 `get_auth_url` 获取授权链接。如果已配置 `CHANJET_REDIRECT_URI`，可以省略 `redirect_uri`：

```json
{
  "redirect_uri": "https://example.com/oauth/callback",
  "state": "optional-state"
}
```

2. 在浏览器打开授权链接，完成畅捷通账号授权。该回调域名必须先在畅捷通开放平台完成可信域名验证。
3. 从回调地址里取得 `code`。
4. 调用 `oauth_complete_setup` 保存该账号 token。如果已配置 `CHANJET_REDIRECT_URI`，这里也可以省略 `redirect_uri`，但必须和生成授权链接时使用的回调地址一致：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback",
  "account_alias": "company-a"
}
```

`account_alias` 只能使用字母、数字、点、下划线和连字符，例如 `company-a`、`client_001`。第一次保存账号时会自动设为 active account。后续调用业务接口时会自动读取该账号 token；如果 token 缺失、过期或接口返回 token 失效，服务会使用 refresh token 自动刷新一次并重试。

## 多客户端授权

不同 MCP 客户端可以使用不同的 `redirect_uri` 和 token 文件。每个 `redirect_uri` 所属域名都需要在畅捷通开放平台完成可信域名验证：下载 `CHANJET_CHECK.txt`，上传到域名根目录，例如 `https://example.com/CHANJET_CHECK.txt`，确认公网可访问后添加可信域名。

共用授权时，多个客户端配置同一个 `CHANJET_REDIRECT_URI` 和同一个 `CHANJET_TOKEN_STORE_PATH`。隔离授权时，为每个客户端配置不同的 `CHANJET_REDIRECT_URI`、`CHANJET_TOKEN_STORE_PATH` 和 `CHANJET_ACTIVE_ACCOUNT`。

Cursor 示例：

```json
{
  "CHANJET_ACTIVE_ACCOUNT": "cursor-company",
  "CHANJET_TOKEN_STORE_PATH": "/Users/sun/Documents/Cursor/SP/.chanjet_tokens.cursor.json",
  "CHANJET_REDIRECT_URI": "https://cursor.example.com/oauth/callback"
}
```

Claude 示例：

```json
{
  "CHANJET_ACTIVE_ACCOUNT": "claude-company",
  "CHANJET_TOKEN_STORE_PATH": "/Users/sun/Documents/Cursor/SP/.chanjet_tokens.claude.json",
  "CHANJET_REDIRECT_URI": "https://claude.example.com/oauth/callback"
}
```

## 运行

```bash
.venv/bin/chanjet-mcp
```

也可以直接运行模块：

```bash
.venv/bin/python -m chanjet_tcloud_mcp
```

兼容命令别名：

```bash
.venv/bin/chanjet-tcloud-mcp
.venv/bin/hyc-mcp
.venv/bin/hsy-mcp
.venv/bin/ydz-mcp
.venv/bin/hkj-mcp
```

## MCP 客户端配置示例

```json
{
  "mcpServers": {
    "chanjet-mcp": {
      "command": "/Users/sun/Documents/Cursor/SP/.venv/bin/python",
      "args": ["-m", "chanjet_tcloud_mcp"],
      "env": {
        "CHANJET_APP_KEY": "your_app_key",
        "CHANJET_APP_SECRET": "your_app_secret",
        "CHANJET_ACTIVE_ACCOUNT": "company-a",
        "CHANJET_TOKEN_STORE_PATH": "/Users/sun/Documents/Cursor/SP/.chanjet_tokens.json",
        "CHANJET_REDIRECT_URI": "https://example.com/oauth/callback"
      }
    }
  }
}
```

如果客户端支持 `cwd`，也可以把 `command` 改为 `/Users/sun/Documents/Cursor/SP/.venv/bin/chanjet-mcp` 并设置 `cwd` 为项目目录；如果提示 `mcpServers.chanjet-mcp: Invalid input`，通常说明该客户端不接受 `cwd` 字段，使用上面的兼容写法。

## 工具列表

推荐客户端流程：

1. 调用 `diagnose_config` 确认配置和账号状态。
2. 调用 `search_api_templates` 用中文业务词直接查找可调用模板。
3. 调用 `call_api_smart` 按官方模板自动解析中文字段并路由到对应产品接口。

如果客户端需要更细控制，也可以继续使用旧流程：先调用 `search_*_docs` 找模块，再调用 `get_api_call_template` 生成模板，最后按模板调用 `call_api_template`、`call_tplus_api`、`call_hyc_api`、`call_hsy_api`、`call_ydz_api` 或 `call_hkj_api`。

`diagnose_config`

返回不含密钥和 token 的安全诊断结果：

```json
{
  "ok": true,
  "data": {
    "settings": {
      "has_app_key": true,
      "has_app_secret": true,
      "has_redirect_uri": true,
      "token_store_path": "/path/to/.chanjet_tokens.json"
    },
    "accounts": {
      "active_account": "company-a",
      "stored_account_count": 1,
      "active_account_exists": true,
      "has_active_open_token": true,
      "has_active_refresh_token": true,
      "active_token_expired": false
    },
    "capabilities": {
      "documentation_lookup": true,
      "oauth_url_generation": true,
      "token_exchange": true,
      "business_api_calls": true
    },
    "issues": []
  }
}
```

如果缺少配置，`issues` 会返回 `missing_app_key`、`missing_app_secret`、`missing_redirect_uri`、`missing_token` 等可读问题和修复建议。

`get_api_call_template`

从官方文档详情里提取接口地址和调用参数模板。`product` 支持 `tplus`/`tcloud`、`hyc`/`zplus`、`hsy`/`haoshengyi`、`ydz`/`finance`、`hkj`/`accounting`。

参数：

```json
{
  "product": "tplus",
  "parent_code": "t+jcda",
  "module_code": "t+ck",
  "api_name": "查询"
}
```

返回：

```json
{
  "ok": true,
  "data": {
    "product": {
      "code": "tcloud",
      "tool": "call_tplus_api"
    },
    "module": {
      "parent_code": "t+jcda",
      "module_code": "t+ck"
    },
    "templates": [
      {
        "api_name": "仓库查询",
        "path": "/tplus/api/v2/warehouse/Query",
        "method": "POST",
        "tool": "call_tplus_api",
        "arguments": {
          "path": "/tplus/api/v2/warehouse/Query",
          "method": "POST",
          "body": {},
          "query": {},
          "headers": {},
          "account_alias": null
        }
      }
    ]
  }
}
```

`search_api_templates`

按业务关键词搜索官方文档，并直接返回可编辑调用模板。客户端不需要先判断应该调用哪个 `search_*_docs`。

参数：

```json
{
  "query": "仓库",
  "product": "tplus",
  "api_name": "查询",
  "limit": 5
}
```

`product` 可省略；省略时会依次搜索 T+Cloud、好业财、好生意、易代账和好会计。返回的每个模板都包含 `product`、`module`、`tool` 和 `arguments`。

`get_tplus_reference_codes`

获取 T+ 单据类型业务编码对照表和业务类型对照表。不知道单据类型 `bizCode` 或业务类型 `BusinessType` 时，先调用此工具。

数据来源：

- 单据类型：`tcloud/t+xdescription/t+vouchertype`
- 业务类型：`tcloud/t+xdescription/t+busitype`

参数：

```json
{
  "query": "销货"
}
```

`query` 可省略；省略时返回完整对照表。可按编码或名称筛选，例如 `SA04`、`销货单`、`02`、`采购退货`。

使用说明：

1. 不知道单据类型 `bizCode` 时，用单据名称查询。

```json
{
  "query": "销货单"
}
```

返回的 `voucher_types` 里找到对应 `code`，例如 `SA04`。后续调用 `query_tplus_voucher_list` 时把它作为 `biz_code`。

2. 不知道业务类型 `BusinessType` 时，用业务类型名称查询。

```json
{
  "query": "采购退货"
}
```

返回的 `business_types` 里找到对应 `code`，例如 `02`。后续调用 T+ 业务接口时把它放进官方接口要求的业务参数字段，例如 `BusinessType`。

3. 如果不确定关键词属于哪张表，可以直接传业务词。

```json
{
  "query": "退货"
}
```

工具会同时筛选 `voucher_types` 和 `business_types`；调用方根据返回项选择单据类型编码或业务类型编码。

返回：

```json
{
  "ok": true,
  "data": {
    "voucher_types": [
      {
        "code": "SA04",
        "name": "销货单",
        "raw": {}
      }
    ],
    "business_types": [
      {
        "code": "02",
        "name": "采购退货",
        "raw": {}
      }
    ],
    "source_docs": {
      "voucher_types": {
        "product": "tcloud",
        "parent_code": "t+xdescription",
        "module_code": "t+vouchertype"
      },
      "business_types": {
        "product": "tcloud",
        "parent_code": "t+xdescription",
        "module_code": "t+busitype"
      }
    }
  }
}
```

`get_tplus_voucher_list_fields`

获取 T+ 单据列表查询项字段和显示栏目字段。不知道列表接口的 `body.param` 查询字段，或不知道 `display_fields` 应该传什么时，先调用此工具。

数据来源：官方 `tcloud/t+dj/djlbcxfz` 单据列表查询辅助页面。该页面对应两个辅助接口：

- 查询项：`/tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode`
- 栏目项：`/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`

参数：

```json
{
  "biz_code": "SA04",
  "query": "客户",
  "account_alias": "company-a"
}
```

`query` 可省略；省略时返回当前单据类型的完整查询项和栏目项。可按字段编码或中文名称筛选，例如 `Code`、`单据编号`、`CustomerName`、`客户`。

返回：

```json
{
  "ok": true,
  "data": {
    "biz_code": "SA04",
    "query_fields": [
      {
        "field": "Code",
        "label": "单据编号",
        "raw": {}
      }
    ],
    "display_fields": [
      {
        "field": "CustomerName",
        "label": "客户",
        "raw": {}
      }
    ],
    "source_doc": {
      "product": "tcloud",
      "parent_code": "t+dj",
      "module_code": "djlbcxfz"
    }
  }
}
```

使用说明：

1. 查询项字段用于构造列表接口的 `body.param`。例如返回 `query_fields` 里有 `Code` / `单据编号`，就可以在请求体里按官方接口要求传入对应查询条件。
2. 显示栏目字段用于 `query_tplus_voucher_list.display_fields`。可以传中文名，工具会匹配成真实字段并注入 `body.param.selectFields`。
3. 不知道 `biz_code` 时，先调用 `get_tplus_reference_codes` 查询单据类型编码。

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

`call_api_smart`

推荐优先使用的智能调用工具，支持 T+Cloud、HYC/ZPlus、HSY、YDZ/Finance 和 HKJ/Accounting。它会先读取官方接口模板，再把用户传入的中文字段解析成真实接口字段，最后自动路由到对应产品接口。解析不到字段时返回统一错误结构，不会静默调用错误请求。

参数示例：

```json
{
  "product": "hyc",
  "parent_code": "zjjcda",
  "module_code": "ck",
  "api_name": "新增",
  "fields": {
    "仓库编码": "WH001",
    "仓库名称": "上海仓"
  },
  "body_overrides": {
    "statusEnum": "A"
  },
  "account_alias": "company-a"
}
```

处理规则：

1. `fields` 的键可以是官方文档中的中文字段名，例如 `仓库编码`。
2. 工具会先从官方接口字段说明解析中文字段；如果文档没有字段说明，则使用官方请求示例里的真实字段名做精确匹配 fallback。
3. 解析后的字段会写入请求体。如果官方示例包含 `param` 对象，则默认写入 `body.param`；如果官方示例是对象数组，则写入第一个数组元素；否则写入请求体顶层。
4. `body_overrides` 最后深度合并，显式覆盖自动解析出的字段。
5. T+ 接口还支持 `voucher_name`、`business_type_name`、`filters` 和 `display_fields`，用于自动解析单据类型、业务类型、查询项和显示栏目。

返回：

```json
{
  "ok": true,
  "data": {
    "template": {},
    "resolved": {
      "product_code": "zplus",
      "matched_fields": [
        {
          "requested": "仓库编码",
          "field": "code",
          "path": ["code"]
        }
      ],
      "unmatched_fields": []
    },
    "request": {
      "path": "/accounting/openapi/cc/warehouse/create/123",
      "method": "POST",
      "body": {
        "code": "WH001"
      }
    },
    "data": {}
  }
}
```

`call_tplus_api_smart`

调用 T+ 接口前自动参考对应官方接口的请求示例，再合并自然语言字段和显式覆盖参数。适合“知道要调用哪个文档模块/接口，但希望服务端自动查编码、查字段、组装请求”的场景。

必须提供官方文档定位参数：

- `parent_code`
- `module_code`
- `api_name`

工具会先调用 `get_api_call_template(product="tplus", ...)`，以官方请求示例作为基础请求；然后按需调用 `get_tplus_reference_codes` 和 `get_tplus_voucher_list_fields`。

参数示例：

```json
{
  "parent_code": "t+xs",
  "module_code": "saleDelivery",
  "api_name": "列表查询",
  "voucher_name": "销货单",
  "business_type_name": "采购退货",
  "filters": {
    "客户": "客户A"
  },
  "display_fields": ["单据编号", "金额"],
  "body_overrides": {
    "param": {
      "pageSize": 50
    }
  },
  "account_alias": "company-a"
}
```

处理规则：

1. `voucher_name` 会解析成 `biz_code`，例如 `销货单` -> `SA04`。
2. `business_type_name` 会解析成 `BusinessType`，例如 `采购退货` -> `02`。
3. `filters` 的中文键会按查询项字段匹配成真实字段，然后写入 `body.param`。
4. `display_fields` 的中文栏目名会匹配成真实字段，然后写入 `body.param.selectFields`。
5. `body_overrides` 最后合并，可覆盖官方示例或自动解析出的字段。
6. 如果查询项或栏目项无法匹配，工具返回统一错误结构，不会静默调用错误请求。

返回：

```json
{
  "ok": true,
  "data": {
    "template": {},
    "resolved": {
      "biz_code": "SA04",
      "business_type": "02",
      "matched_filter_fields": [],
      "matched_display_fields": []
    },
    "request": {
      "path": "/tplus/api/v2/saleDelivery/Query",
      "method": "POST",
      "body": {}
    },
    "data": {}
  }
}
```

`call_api_template`

根据官方文档模板自动选择对应产品调用工具。客户端只需要提供产品、模块编码、可选接口名和业务参数，不需要自己选择 `call_tplus_api` / `call_hyc_api` 等底层工具。

参数：

```json
{
  "product": "tplus",
  "parent_code": "t+jcda",
  "module_code": "t+ck",
  "api_name": "查询",
  "account_alias": "company-a",
  "body": {
    "param": {
      "Code": "01"
    }
  }
}
```

返回：

```json
{
  "ok": true,
  "data": {
    "template": {
      "api_name": "仓库查询",
      "path": "/tplus/api/v2/warehouse/Query",
      "tool": "call_tplus_api"
    },
    "request": {
      "path": "/tplus/api/v2/warehouse/Query",
      "method": "POST",
      "body": {
        "param": {
          "Code": "01"
        }
      },
      "query": {},
      "headers": {},
      "account_alias": "company-a"
    },
    "data": {}
  }
}
```

`diagnose_config`、`get_api_call_template`、`search_api_templates`、`get_tplus_reference_codes`、`get_tplus_voucher_list_fields`、`call_api_smart`、`call_tplus_api_smart` 和 `call_api_template` 使用统一错误结构：

```json
{
  "ok": false,
  "error": {
    "code": "invalid_argument",
    "message": "Unsupported product: unknown",
    "hint": "Use one of: tplus, tcloud, hyc, zplus, hsy, haoshengyi, ydz, finance, hkj, accounting.",
    "trace_id": null
  }
}
```

`list_tcloud_modules`

返回官方 T+Cloud 文档模块树。

`list_hyc_modules`

返回官方好业财 HYC/ZPlus 文档模块树。

`list_hsy_modules`

返回官方好生意 HSY 文档模块树。

`list_ydz_modules`

返回官方易代账 YDZ/Finance 文档模块树。

`list_hkj_modules`

返回官方好会计 HKJ/Accounting 文档模块树。

`get_tcloud_doc`

参数：

```json
{
  "parent_code": "t+jcda",
  "module_code": "t+ck"
}
```

返回仓库模块的官方接口详情。

`get_hyc_doc`

参数：

```json
{
  "parent_code": "zjjcda",
  "module_code": "ck"
}
```

返回好业财仓库模块的官方接口详情。

`get_hsy_doc`

参数：

```json
{
  "parent_code": "hsyxxdy",
  "module_code": "hsy_product"
}
```

返回好生意模块的官方接口详情。当前官方 `hsy` 产品文档树可能为空；工具会随官方文档更新自动返回新增模块。

`get_ydz_doc`

参数：

```json
{
  "parent_code": "ydzjcda",
  "module_code": "ck"
}
```

返回易代账仓库模块的官方接口详情。

`get_hkj_doc`

参数：

```json
{
  "parent_code": "jcda",
  "module_code": "ck"
}
```

返回好会计仓库模块的官方接口详情。

`search_tcloud_docs`

参数：

```json
{
  "query": "仓库",
  "limit": 20
}
```

返回匹配的模块编码、名称和文档路径。

`search_hyc_docs`

参数：

```json
{
  "query": "仓库",
  "limit": 20
}
```

返回匹配的好业财模块编码、名称和文档路径。

`search_hsy_docs`

参数：

```json
{
  "query": "仓库",
  "limit": 20
}
```

返回匹配的好生意模块编码、名称和文档路径。

`search_ydz_docs`

参数：

```json
{
  "query": "仓库",
  "limit": 20
}
```

返回匹配的易代账模块编码、名称和文档路径。

`search_hkj_docs`

参数：

```json
{
  "query": "仓库",
  "limit": 20
}
```

返回匹配的好会计模块编码、名称和文档路径。

`call_tplus_api`

参数示例：

```json
{
  "path": "/tplus/api/v2/warehouse/Query",
  "method": "POST",
  "account_alias": "company-a",
  "body": {
    "param": {
      "Code": "01"
    }
  }
}
```

服务会自动注入：

```json
{
  "appKey": "from CHANJET_APP_KEY",
  "appSecret": "from CHANJET_APP_SECRET",
  "openToken": "from active or selected account",
  "Content-Type": "application/json"
}
```

如果不传 `account_alias`，服务会使用 `CHANJET_ACTIVE_ACCOUNT` 或 token store 中的 active account。

`query_tplus_voucher_list_smart`

自然语言 T+ 单据列表查询工具。推荐用于“查生产加工单列表”“查询所有销货单”这类请求。服务会自动识别 `列表`、`查询`、`所有`、`全部` 等意图，解析单据 `bizCode`，搜索官方文档中的列表查询接口，生成分页和查询体，再调用 T+ 业务接口。

参数示例：

```json
{
  "voucher_name": "生产加工单",
  "intent": "查询所有",
  "module_code": "ManufactureOrderOpenApi",
  "filters": {
    "单据编号": "MO-001"
  },
  "display_fields": ["单据编号", "数量"],
  "page_size": 50,
  "page_index": 1,
  "account_alias": "company-a"
}
```

处理规则：

1. `voucher_name` 先通过官方单据类型文档解析 `bizCode`，官方缺失时使用少量稳定兜底映射，例如 `生产加工单 -> MP05`。
2. 工具会搜索官方文档并优先选择 `FindVoucherList` 或名称包含“列表查询”的接口。
3. `filters` 的中文字段会按查询项解析并写入 `body.param.paramDic`。
4. `display_fields` 会按栏目项解析并写入 `body.param.selectFields`。
5. `page_size` 和 `page_index` 会写入 `body.param.pageSize` 和 `body.param.pageIndex`。
6. 如果误传 `module_code: "ManufactureOrderOpenApi"`，工具会把它当作接口类名兼容处理，继续按 `voucher_name` 搜索官方文档。

返回值包含实际业务响应、选中的官方模板、最终请求体和解析过程：

```json
{
  "ok": true,
  "data": {
    "data": {},
    "template": {},
    "request": {
      "path": "/tplus/api/v2/ManufactureOrderOpenApi/FindVoucherList",
      "method": "POST",
      "body": {
        "param": {
          "pageSize": 50,
          "pageIndex": 1,
          "paramDic": {
            "Code": "MO-001"
          },
          "selectFields": ["Code", "Quantity"]
        }
      }
    },
    "resolved": {
      "biz_code": "MP05",
      "biz_code_source": "fallback",
      "matched_filter_fields": [],
      "matched_display_fields": []
    }
  }
}
```

`query_tplus_voucher_list`

查询 T+ 单据列表的专用工具。服务会先调用官方单据列表查询辅助接口，获取当前单据编码的查询项字段和显示栏目字段，再把 `display_fields` 自动匹配成真实字段并注入到列表查询请求中。

辅助接口来源于 `tcloud/t+dj/djlbcxfz`：

- 查询项：`/tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode`
- 栏目项：`/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode`

如果不知道 `biz_code` 应该传什么，或业务参数里需要 `BusinessType` 但不知道编码，先调用 `get_tplus_reference_codes` 查询对照表。

如果不知道 `body.param` 支持哪些查询字段，或不知道 `display_fields` 支持哪些显示栏目，先调用 `get_tplus_voucher_list_fields`。

参数示例：

```json
{
  "biz_code": "SA03",
  "path": "/tplus/api/v2/saleDelivery/Query",
  "method": "POST",
  "account_alias": "company-a",
  "display_fields": ["单据编号", "客户", "金额"],
  "body": {
    "param": {
      "pageIndex": 1,
      "pageSize": 20
    }
  }
}
```

返回值包含实际列表查询响应、全部可用查询项字段、全部可用显示字段、已匹配字段和未匹配字段：

```json
{
  "data": {},
  "query_fields": [],
  "display_fields": [],
  "matched_display_fields": [],
  "unmatched_display_fields": []
}
```

如果请求体中已存在 `selectFields`、`fields`、`columns` 或 `select`，服务不会覆盖调用方已有的字段选择。

`call_hyc_api`

参数示例：

```json
{
  "path": "/accounting/openapi/cc/warehouse/list/123456",
  "method": "POST",
  "account_alias": "company-a",
  "body": {
    "pageSize": 20,
    "pageNo": 1
  }
}
```

服务会自动注入与 T+Cloud 相同的畅捷通开放平台请求头。

`call_hsy_api`

参数示例：

```json
{
  "path": "/accounting/openapi/cc/warehouse/list/123456",
  "method": "POST",
  "account_alias": "company-a",
  "body": {
    "pageSize": 20,
    "pageNo": 1
  }
}
```

服务会自动注入与 T+Cloud 相同的畅捷通开放平台请求头。好生意官方文档当前可能还没有模块树，具体业务路径以官方文档后续返回为准。

`call_ydz_api`

参数示例：

```json
{
  "path": "/accounting/document/integration/warehouse/batchUpsertt/123456",
  "method": "POST",
  "account_alias": "company-a",
  "body": [
    {
      "id": "WH001",
      "code": "WH001",
      "name": "仓库",
      "statusEnum": "A"
    }
  ]
}
```

服务会自动注入与 T+Cloud 相同的畅捷通开放平台请求头。

`call_hkj_api`

参数示例：

```json
{
  "path": "/accounting/document/integration/warehouse/batchUpsertt/123456",
  "method": "POST",
  "account_alias": "company-a",
  "body": [
    {
      "id": "HKJ001",
      "code": "HKJ001",
      "name": "仓库",
      "statusEnum": "A"
    }
  ]
}
```

服务会自动注入与 T+Cloud 相同的畅捷通开放平台请求头。

`get_auth_url`

参数：

```json
{
  "redirect_uri": "https://example.com/oauth/callback",
  "state": "optional-state"
}
```

如果已配置 `CHANJET_REDIRECT_URI`，`redirect_uri` 可省略。

`exchange_token`

参数：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback"
}
```

如果已配置 `CHANJET_REDIRECT_URI`，`redirect_uri` 可省略。

`oauth_complete_setup`

参数：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback",
  "account_alias": "company-a"
}
```

如果已配置 `CHANJET_REDIRECT_URI`，`redirect_uri` 可省略。

返回安全账号摘要，不返回真实 token。

`list_auth_accounts`

返回所有已授权账号的安全摘要。

`get_active_account`

返回当前 active account 的安全摘要。

`set_active_account`

参数：

```json
{
  "account_alias": "company-a"
}
```

`delete_auth_account`

参数：

```json
{
  "account_alias": "company-a"
}
```

`refresh_token`

参数：

```json
{
  "refresh_token": "optional_refresh_token"
}
```

如果未传 `refresh_token`，服务会读取 `CHANJET_REFRESH_TOKEN`。

## 开发验证

不安装包时运行单元测试：

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

安装后运行：

```bash
.venv/bin/python -m unittest discover -s tests -v
```
