# Chanjet MCP Server

独立 Python MCP 服务，用于把畅捷通 T+Cloud、好业财（HYC/ZPlus）、易代账（YDZ/Finance）和好会计（HKJ/Accounting）OpenAPI 文档与业务接口暴露给 MCP 客户端。

## 功能

- 查询 T+Cloud 官方 API 文档模块树。
- 查询好业财 HYC/ZPlus 官方 API 文档模块树。
- 查询易代账 YDZ/Finance 官方 API 文档模块树。
- 查询好会计 HKJ/Accounting 官方 API 文档模块树。
- 按模块编码读取官方接口详情。
- 按关键词搜索 T+Cloud、HYC/ZPlus、YDZ/Finance 或 HKJ/Accounting 文档模块。
- 通用调用任意 `/tplus/api/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 HYC/ZPlus `/accounting/openapi/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
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
```

`CHANJET_APP_KEY` 和 `CHANJET_APP_SECRET` 是应用级凭据。账号级 `openToken` / `refreshToken` 推荐通过 OAuth setup 自动写入本地 `.chanjet_tokens.json`，该文件已加入 `.gitignore`。

兼容旧用法：仍可在 `.env` 中配置 `CHANJET_OPEN_TOKEN` 和 `CHANJET_REFRESH_TOKEN` 作为单账号 fallback。如果只使用文档查询工具，可以暂时不配置业务接口凭据。

## 首次 OAuth 授权

1. 调用 `get_auth_url` 获取授权链接：

```json
{
  "redirect_uri": "https://example.com/oauth/callback",
  "state": "optional-state"
}
```

2. 在浏览器打开授权链接，完成畅捷通账号授权。
3. 从回调地址里取得 `code`。
4. 调用 `oauth_complete_setup` 保存该账号 token：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback",
  "account_alias": "company-a"
}
```

`account_alias` 只能使用字母、数字、点、下划线和连字符，例如 `company-a`、`client_001`。第一次保存账号时会自动设为 active account。后续调用业务接口时会自动读取该账号 token；如果 token 缺失、过期或接口返回 token 失效，服务会使用 refresh token 自动刷新一次并重试。

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
        "CHANJET_TOKEN_STORE_PATH": "/Users/sun/Documents/Cursor/SP/.chanjet_tokens.json"
      }
    }
  }
}
```

如果客户端支持 `cwd`，也可以把 `command` 改为 `/Users/sun/Documents/Cursor/SP/.venv/bin/chanjet-mcp` 并设置 `cwd` 为项目目录；如果提示 `mcpServers.chanjet-mcp: Invalid input`，通常说明该客户端不接受 `cwd` 字段，使用上面的兼容写法。

## 工具列表

`list_tcloud_modules`

返回官方 T+Cloud 文档模块树。

`list_hyc_modules`

返回官方好业财 HYC/ZPlus 文档模块树。

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

`exchange_token`

参数：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback"
}
```

`oauth_complete_setup`

参数：

```json
{
  "code": "temporary_authorization_code",
  "redirect_uri": "https://example.com/oauth/callback",
  "account_alias": "company-a"
}
```

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
