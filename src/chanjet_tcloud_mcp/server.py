from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import ChanjetTCloudClient
from .settings import ChanjetSettings


settings = ChanjetSettings.from_env_file()
client = ChanjetTCloudClient(settings=settings)
mcp = FastMCP("chanjet-tcloud")


@mcp.tool()
def list_tcloud_modules() -> dict[str, Any]:
    """Return the official Chanjet T+Cloud API document module tree."""
    return client.list_tcloud_modules()


@mcp.tool()
def list_hyc_modules() -> dict[str, Any]:
    """Return the official Chanjet HYC/ZPlus API document module tree."""
    return client.list_hyc_modules()


@mcp.tool()
def get_tcloud_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a T+Cloud module path."""
    return client.get_tcloud_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def get_hyc_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a HYC/ZPlus module path."""
    return client.get_hyc_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def search_tcloud_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search T+Cloud document modules by code or display name."""
    return client.search_tcloud_docs(query=query, limit=limit)


@mcp.tool()
def search_hyc_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search HYC/ZPlus document modules by code or display name."""
    return client.search_hyc_docs(query=query, limit=limit)


@mcp.tool()
def call_tplus_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Call an arbitrary T+ OpenAPI path using configured Chanjet credentials."""
    return client.call_tplus_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
    )


@mcp.tool()
def call_hyc_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Call an arbitrary HYC/ZPlus OpenAPI path using configured credentials."""
    return client.call_hyc_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
    )


@mcp.tool()
def get_auth_url(redirect_uri: str, state: str | None = None) -> str:
    """Build a Chanjet OAuth authorization URL."""
    return client.get_auth_url(redirect_uri=redirect_uri, state=state)


@mcp.tool()
def exchange_token(code: str, redirect_uri: str) -> dict[str, Any]:
    """Exchange a temporary authorization code for token data."""
    return client.exchange_token(code=code, redirect_uri=redirect_uri)


@mcp.tool()
def refresh_token(refresh_token: str | None = None) -> dict[str, Any]:
    """Refresh an access token using a refresh token."""
    return client.refresh_token(refresh_token=refresh_token)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
