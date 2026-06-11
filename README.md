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
3. 调用 `call_api_template` 按模板自动路由到对应产品接口。

如果客户端需要更细控制，也可以继续使用旧流程：先调用 `search_*_docs` 找模块，再调用 `get_api_call_template` 生成模板，最后按模板调用 `call_tplus_api`、`call_hyc_api`、`call_hsy_api`、`call_ydz_api` 或 `call_hkj_api`。

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

`diagnose_config`、`get_api_call_template`、`search_api_templates` 和 `call_api_template` 使用统一错误结构：

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

`query_tplus_voucher_list`

查询 T+ 单据列表的专用工具。服务会先调用官方栏目辅助接口
`/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode` 获取当前单据编码的全部列表显示字段，再把 `display_fields` 自动匹配成真实字段并注入到列表查询请求中。

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

返回值包含实际列表查询响应、全部可用显示字段、已匹配字段和未匹配字段：

```json
{
  "data": {},
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
