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
def list_hsy_modules() -> dict[str, Any]:
    """Return the official Chanjet HSY API document module tree."""
    return client.list_hsy_modules()


@mcp.tool()
def list_ydz_modules() -> dict[str, Any]:
    """Return the official Chanjet YDZ/Finance API document module tree."""
    return client.list_ydz_modules()


@mcp.tool()
def list_hkj_modules() -> dict[str, Any]:
    """Return the official Chanjet HKJ/Accounting API document module tree."""
    return client.list_hkj_modules()


@mcp.tool()
def get_tcloud_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a T+Cloud module path."""
    return client.get_tcloud_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def get_hyc_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a HYC/ZPlus module path."""
    return client.get_hyc_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def get_hsy_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a HSY module path."""
    return client.get_hsy_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def get_ydz_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a YDZ/Finance module path."""
    return client.get_ydz_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def get_hkj_doc(parent_code: str, module_code: str) -> dict[str, Any]:
    """Return official document/API details for a HKJ/Accounting module path."""
    return client.get_hkj_doc(parent_code=parent_code, module_code=module_code)


@mcp.tool()
def search_tcloud_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search T+Cloud document modules by code or display name."""
    return client.search_tcloud_docs(query=query, limit=limit)


@mcp.tool()
def search_hyc_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search HYC/ZPlus document modules by code or display name."""
    return client.search_hyc_docs(query=query, limit=limit)


@mcp.tool()
def search_hsy_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search HSY document modules by code or display name."""
    return client.search_hsy_docs(query=query, limit=limit)


@mcp.tool()
def search_ydz_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search YDZ/Finance document modules by code or display name."""
    return client.search_ydz_docs(query=query, limit=limit)


@mcp.tool()
def search_hkj_docs(query: str, limit: int = 20) -> list[dict[str, Any]]:
    """Search HKJ/Accounting document modules by code or display name."""
    return client.search_hkj_docs(query=query, limit=limit)


@mcp.tool()
def diagnose_config() -> dict[str, Any]:
    """Return a safe readiness report for MCP client configuration."""
    return client.safe_diagnose_config()


@mcp.tool()
def call_natural(
    user_input: str,
    product: str | None = None,
    dry_run: bool = False,
    fields: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    page_size: int = 20,
    page_index: int = 1,
    headers: dict[str, str] | None = None,
    query: dict[str, Any] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Route a natural-language request to the safest matching Chanjet tool.

    This deterministic router parses product, action, business object, fields,
    filters, and display columns. Only T+ voucher document list requests use
    voucher_name/bizCode routing; non-voucher APIs are resolved through official
    API templates. It calls only high-confidence routes; otherwise it returns
    ranked candidates for the LLM/client to inspect.
    """
    return client.safe_call_natural(
        user_input=user_input,
        product=product,
        dry_run=dry_run,
        fields=fields,
        filters=filters,
        display_fields=display_fields,
        body_overrides=body_overrides,
        page_size=page_size,
        page_index=page_index,
        headers=headers,
        query=query,
        account_alias=account_alias,
    )


@mcp.tool()
def get_api_call_template(
    product: str,
    parent_code: str,
    module_code: str,
    api_name: str | None = None,
) -> dict[str, Any]:
    """Build ready-to-edit call templates from official API documentation."""
    return client.safe_get_api_call_template(
        product=product,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
    )


@mcp.tool()
def search_api_templates(
    query: str,
    product: str | None = None,
    api_name: str | None = None,
    limit: int = 20,
) -> dict[str, Any]:
    """Search official docs and return ready-to-edit API call templates."""
    return client.safe_search_api_templates(
        query=query,
        product=product,
        api_name=api_name,
        limit=limit,
    )


@mcp.tool()
def call_api_smart(
    product: str,
    parent_code: str,
    module_code: str,
    api_name: str | None = None,
    fields: dict[str, Any] | None = None,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
    method: str | None = None,
    voucher_name: str | None = None,
    biz_code: str | None = None,
    business_type_name: str | None = None,
    business_type: str | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
) -> dict[str, Any]:
    """Call any supported product API from the official template.

    User-facing Chinese field names in fields are resolved to real API request
    fields before the request is sent. T+ calls also support voucher/business
    type and voucher list field resolution.
    """
    return client.safe_call_api_smart(
        product=product,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        fields=fields,
        body_overrides=body_overrides,
        query=query,
        headers=headers,
        account_alias=account_alias,
        method=method,
        voucher_name=voucher_name,
        biz_code=biz_code,
        business_type_name=business_type_name,
        business_type=business_type,
        filters=filters,
        display_fields=display_fields,
    )


@mcp.tool()
def call_api_template(
    product: str,
    parent_code: str,
    module_code: str,
    api_name: str | None = None,
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
    method: str | None = None,
) -> dict[str, Any]:
    """Find an official API template and route the call to the right product tool.

    For T+ calls, if the request needs a voucher bizCode or BusinessType and
    the exact code is unknown, call get_tplus_reference_codes first.
    """
    return client.safe_call_api_template(
        product=product,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
        method=method,
    )


@mcp.tool()
def call_tplus_api_smart(
    parent_code: str,
    module_code: str,
    api_name: str | None = None,
    voucher_name: str | None = None,
    biz_code: str | None = None,
    business_type_name: str | None = None,
    business_type: str | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
    method: str | None = None,
) -> dict[str, Any]:
    """Call a T+ API after consulting the official request example.

    Use this for more automatic T+ calls. It first loads the matching official
    API template, then resolves voucher_name, business_type_name, natural
    language filter names, and display_fields before sending the request.
    """
    return client.safe_call_tplus_api_smart(
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        voucher_name=voucher_name,
        biz_code=biz_code,
        business_type_name=business_type_name,
        business_type=business_type,
        filters=filters,
        display_fields=display_fields,
        body_overrides=body_overrides,
        query=query,
        headers=headers,
        account_alias=account_alias,
        method=method,
    )


@mcp.tool()
def get_tplus_reference_codes(query: str | None = None) -> dict[str, Any]:
    """Return T+ voucher bizCode and BusinessType reference rows.

    Call this first when a T+ request needs a voucher bizCode or BusinessType
    and the exact code is unknown. Search by code or name, for example SA04,
    销货单, 02, or 采购退货.
    """
    return client.safe_get_tplus_reference_codes(query=query)


@mcp.tool()
def get_tplus_voucher_list_fields(
    biz_code: str,
    query: str | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Return T+ voucher list query fields and display columns for a bizCode.

    Call this before query_tplus_voucher_list when valid body.param query
    fields or display_fields are unknown. The helper APIs are documented by
    tcloud/t+dj/djlbcxfz.
    """
    return client.safe_get_tplus_voucher_list_fields(
        biz_code=biz_code,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def call_tplus_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> Any:
    """Call an arbitrary T+ OpenAPI path using configured Chanjet credentials.

    If the request body needs BusinessType and the exact code is unknown,
    call get_tplus_reference_codes first and use a business_types code.
    """
    return client.call_tplus_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def query_tplus_voucher_list(
    biz_code: str,
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    display_fields: list[str] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Query a T+ voucher list after preloading and matching display fields.

    If biz_code is unknown, call get_tplus_reference_codes first and use a
    voucher_types code as biz_code. If body.param query fields or display
    columns are unknown, call get_tplus_voucher_list_fields first.
    """
    return client.query_tplus_voucher_list(
        biz_code=biz_code,
        path=path,
        method=method,
        body=body,
        display_fields=display_fields,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def query_tplus_voucher_list_smart(
    voucher_name: str,
    intent: str | None = None,
    filters: dict[str, Any] | None = None,
    display_fields: list[str] | None = None,
    page_size: int = 20,
    page_index: int = 1,
    body_overrides: dict[str, Any] | list[Any] | None = None,
    parent_code: str | None = None,
    module_code: str | None = None,
    api_name: str | None = None,
    path: str | None = None,
    method: str | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> dict[str, Any]:
    """Query a T+ voucher list from natural voucher name and list intent.

    Use this for requests like 查询所有生产加工单. The service resolves bizCode,
    finds the official list-query template, builds pageSize/pageIndex/paramDic,
    resolves display_fields, and calls the T+ API.
    """
    return client.safe_query_tplus_voucher_list_smart(
        voucher_name=voucher_name,
        intent=intent,
        filters=filters,
        display_fields=display_fields,
        page_size=page_size,
        page_index=page_index,
        body_overrides=body_overrides,
        parent_code=parent_code,
        module_code=module_code,
        api_name=api_name,
        path=path,
        method=method,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def call_hyc_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> Any:
    """Call an arbitrary HYC/ZPlus OpenAPI path using configured credentials."""
    return client.call_hyc_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def call_hsy_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> Any:
    """Call an arbitrary HSY OpenAPI path using configured credentials."""
    return client.call_hsy_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def call_ydz_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> Any:
    """Call an arbitrary YDZ/Finance OpenAPI path using configured credentials."""
    return client.call_ydz_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def call_hkj_api(
    path: str,
    method: str = "POST",
    body: dict[str, Any] | list[Any] | None = None,
    query: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    account_alias: str | None = None,
) -> Any:
    """Call an arbitrary HKJ/Accounting OpenAPI path using configured credentials."""
    return client.call_hkj_api(
        path=path,
        method=method,
        body=body,
        query=query,
        headers=headers,
        account_alias=account_alias,
    )


@mcp.tool()
def get_auth_url(redirect_uri: str | None = None, state: str | None = None) -> str:
    """Build a Chanjet OAuth authorization URL."""
    return client.get_auth_url(redirect_uri=redirect_uri, state=state)


@mcp.tool()
def exchange_token(code: str, redirect_uri: str | None = None) -> dict[str, Any]:
    """Exchange a temporary authorization code for token data."""
    return client.exchange_token(code=code, redirect_uri=redirect_uri)


@mcp.tool()
def oauth_complete_setup(
    code: str,
    account_alias: str,
    redirect_uri: str | None = None,
) -> dict[str, Any]:
    """Exchange an OAuth code and store tokens under a named Chanjet account."""
    return client.oauth_complete_setup(
        code=code,
        account_alias=account_alias,
        redirect_uri=redirect_uri,
    )


@mcp.tool()
def list_auth_accounts() -> list[dict[str, Any]]:
    """Return safe summaries for stored Chanjet authorization accounts."""
    return client.list_auth_accounts()


@mcp.tool()
def get_active_account() -> dict[str, Any] | None:
    """Return the current active Chanjet authorization account summary."""
    return client.get_active_account()


@mcp.tool()
def set_active_account(account_alias: str) -> dict[str, Any]:
    """Set the active Chanjet authorization account."""
    return client.set_active_account(account_alias=account_alias)


@mcp.tool()
def delete_auth_account(account_alias: str) -> dict[str, Any]:
    """Delete a stored Chanjet authorization account."""
    return client.delete_auth_account(account_alias=account_alias)


@mcp.tool()
def refresh_token(refresh_token: str | None = None) -> dict[str, Any]:
    """Refresh an access token using a refresh token."""
    return client.refresh_token(refresh_token=refresh_token)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
