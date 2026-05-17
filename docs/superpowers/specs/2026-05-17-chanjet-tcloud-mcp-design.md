# Chanjet T+Cloud MCP Service Design

## Goal

Build an independent Python MCP server in this directory that exposes Chanjet T+Cloud OpenAPI documentation lookup, OAuth helpers, and authenticated T+ API calls to MCP clients.

## Scope

The first version is intentionally small and usable:

- Read official T+Cloud document module data from Chanjet OpenAPI document endpoints.
- Retrieve official document/API detail by module path.
- Search the T+Cloud module tree by code or display name.
- Call any T+ business API path with credentials injected from environment configuration.
- Generate OAuth authorization URLs, exchange authorization codes for tokens, and refresh tokens.

The service does not include a database, UI, multi-tenant management, background token refresh, or webhook message handling.

## Architecture

The server is a standard Python package under `src/chanjet_tcloud_mcp`. `ChanjetTCloudClient` owns all Chanjet-specific behavior and depends on a small transport interface so tests can run without network access. `server.py` wraps the client in MCP tools using the official Python MCP SDK `FastMCP`.

Configuration is loaded from environment variables and an optional `.env` file. Runtime credentials are never hard-coded.

## MCP Tools

- `list_tcloud_modules`: Return the official T+Cloud module tree.
- `get_tcloud_doc`: Return document/API details for a parent module code and child module code.
- `search_tcloud_docs`: Search module codes and names in the official module tree.
- `call_tplus_api`: Call an arbitrary T+ OpenAPI endpoint with configured credentials.
- `get_auth_url`: Build an OAuth authorization URL.
- `exchange_token`: Exchange an authorization code for token data.
- `refresh_token`: Refresh an access token.

## Configuration

Required for business API calls:

- `CHANJET_APP_KEY`
- `CHANJET_APP_SECRET`
- `CHANJET_OPEN_TOKEN`

Optional:

- `CHANJET_REFRESH_TOKEN`
- `CHANJET_BASE_URL`, default `https://openapi.chanjet.com`
- `CHANJET_DOCS_API_URL`, default `https://openapi.chanjet.com/developer/api`
- `CHANJET_TIMEOUT_SECONDS`, default `30`

## Error Handling

Document APIs return a `result/error/value` envelope. The client unwraps successful values and raises `ChanjetApiError` with the platform code, message, hint, and trace ID for failures.

Business APIs can return multiple shapes, so `call_tplus_api` returns the parsed JSON response as-is unless the HTTP layer fails.

## Testing

Unit tests use fake transports and Python `unittest`, so they do not call real Chanjet services. Verification includes:

- Configuration parsing.
- Document envelope unwrapping and path construction.
- Module tree search.
- Credential injection for T+ API calls.
- OAuth authorization and token request construction.

