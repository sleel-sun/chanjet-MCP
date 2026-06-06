# Chanjet Multi-Account OAuth Design

## Goal

Enable the MCP server to complete a one-time OAuth authorization flow, store tokens for multiple Chanjet accounts, and automatically use or refresh those tokens for full business API access.

## Scope

The server will keep application credentials in `.env` and move account-specific OAuth credentials into a local token store. Users will authorize each account once, name it with an `account_alias`, then call API tools either through the active account or by passing an account alias.

## Storage

- `.env` remains the source for `CHANJET_APP_KEY`, `CHANJET_APP_SECRET`, `CHANJET_BASE_URL`, and `CHANJET_DOCS_API_URL`.
- `CHANJET_ACTIVE_ACCOUNT` may set the default account alias.
- `CHANJET_TOKEN_STORE_PATH` may override the token store path.
- The default token store is `.chanjet_tokens.json` in the project working directory.
- The token store records `active_account` and an `accounts` map keyed by user-defined aliases.
- Each account record stores `open_token`, `refresh_token`, `expires_at`, and selected non-sensitive metadata. Raw token responses are retained only when needed for future compatibility.
- `.chanjet_tokens.json` is git-ignored.

## MCP Tools

Add these tools:

- `oauth_complete_setup(code, redirect_uri, account_alias)`: exchanges an OAuth authorization code, stores the returned tokens under `account_alias`, and makes the account active if no active account exists.
- `list_auth_accounts()`: returns safe account summaries without printing token values.
- `get_active_account()`: returns the current active account summary.
- `set_active_account(account_alias)`: sets the active account in the token store.
- `delete_auth_account(account_alias)`: removes an account and clears active account if it was active.

Existing `get_auth_url`, `exchange_token`, and `refresh_token` remain available for manual/debug use.

## API Calls

All `call_*_api` tools accept an optional `account_alias`. If omitted, the client uses the active account from `.env` or the token store. Before a business API call, the client resolves credentials in this order:

1. Named or active token-store account.
2. Legacy `.env` `CHANJET_OPEN_TOKEN` and `CHANJET_REFRESH_TOKEN` values for backward compatibility.

If an account has a refresh token and the open token is missing or expired, the client refreshes automatically, persists the new token data, and proceeds. If an API response indicates token expiration or invalid token, the client refreshes once and retries the original request.

## Error Handling

- Missing app credentials produce a clear error naming the missing setting.
- Missing active account produces a clear error instructing the user to run OAuth setup or pass `account_alias`.
- Missing refresh token prevents auto-refresh and returns a clear error.
- Invalid account aliases are rejected.
- Token values are never included in account summaries or ordinary error messages.

## Testing

Tests will cover:

- Token store read/write, active-account selection, deletion, and safe summaries.
- OAuth setup stores exchanged tokens under an alias.
- API calls inject the selected account token.
- Missing open token triggers refresh using the account refresh token.
- Expired-token API responses refresh once and retry.
- Legacy `.env` token behavior still works.

## Security Notes

The token store contains secrets and must not be committed. File writes should use owner-only permissions where supported. MCP tools should return only safe summaries unless the existing manual token tools are called explicitly.
