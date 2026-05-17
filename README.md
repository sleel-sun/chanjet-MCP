# Chanjet MCP Server

独立 Python MCP 服务，用于把畅捷通 T+Cloud 和好业财（HYC/ZPlus）OpenAPI 文档与业务接口暴露给 MCP 客户端。

## 功能

- 查询 T+Cloud 官方 API 文档模块树。
- 查询好业财 HYC/ZPlus 官方 API 文档模块树。
- 按模块编码读取官方接口详情。
- 按关键词搜索 T+Cloud 或 HYC/ZPlus 文档模块。
- 通用调用任意 `/tplus/api/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 通用调用任意 HYC/ZPlus `/accounting/openapi/...` 业务接口，自动注入 `appKey`、`appSecret`、`openToken`。
- 生成 OAuth 授权链接、授权码换 token、刷新 token。

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
CHANJET_OPEN_TOKEN=your_open_token
CHANJET_REFRESH_TOKEN=your_refresh_token
```

`CHANJET_OPEN_TOKEN` 是调用 T+Cloud 或 HYC/ZPlus 业务接口时请求头里的 `openToken`。如果只使用文档查询工具，可以暂时不配置业务接口凭据。

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
```

## MCP 客户端配置示例

```json
{
  "mcpServers": {
    "chanjet-mcp": {
      "command": "/Users/sun/Documents/Cursor/SP/.venv/bin/chanjet-mcp",
      "cwd": "/Users/sun/Documents/Cursor/SP",
      "env": {
        "CHANJET_APP_KEY": "your_app_key",
        "CHANJET_APP_SECRET": "your_app_secret",
        "CHANJET_OPEN_TOKEN": "your_open_token",
        "CHANJET_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

## 工具列表

`list_tcloud_modules`

返回官方 T+Cloud 文档模块树。

`list_hyc_modules`

返回官方好业财 HYC/ZPlus 文档模块树。

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

`call_tplus_api`

参数示例：

```json
{
  "path": "/tplus/api/v2/warehouse/Query",
  "method": "POST",
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
  "openToken": "from CHANJET_OPEN_TOKEN",
  "Content-Type": "application/json"
}
```

`call_hyc_api`

参数示例：

```json
{
  "path": "/accounting/openapi/cc/warehouse/list/123456",
  "method": "POST",
  "body": {
    "pageSize": 20,
    "pageNo": 1
  }
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
