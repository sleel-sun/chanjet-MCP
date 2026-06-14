from __future__ import annotations

import copy
import hashlib
import time
import uuid
from dataclasses import replace
from typing import Any
from urllib.parse import quote, urlencode

from .settings import ChanjetSettings
from .token_store import TokenStore
from .transport import HttpTransportError, JsonTransport, UrlLibTransport


TCLOUD_PRODUCT_CODE = "tcloud"
HYC_PRODUCT_CODE = "zplus"
HSY_PRODUCT_CODE = "hsy"
YDZ_PRODUCT_CODE = "finance"
HKJ_PRODUCT_CODE = "accounting"
TPLUS_VOUCHER_COLUMN_SET_PATH = (
    "/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode"
)
TPLUS_VOUCHER_SEARCH_ITEM_PATH = (
    "/tplus/api/v2/VoucherAPIService/GetSearchItemByBizCode"
)
TPLUS_VOUCHER_LIST_FIELD_DOC_PARENT_CODE = "t+dj"
TPLUS_VOUCHER_LIST_FIELD_DOC_MODULE_CODE = "djlbcxfz"
TPLUS_DESCRIPTION_PARENT_CODE = "t+xdescription"
TPLUS_VOUCHER_TYPE_MODULE_CODE = "t+vouchertype"
TPLUS_BUSINESS_TYPE_MODULE_CODE = "t+busitype"
VOUCHER_FIELD_SELECTION_KEYS = {"selectfields", "fields", "columns", "select"}
REFERENCE_CODE_KEYS = (
    "code",
    "bizCode",
    "businessType",
    "BusinessType",
    "value",
    "key",
    "编码",
    "业务编码",
    "单据编码",
    "单据类型编码",
    "业务类型编码",
)
REFERENCE_NAME_KEYS = (
    "name",
    "label",
    "title",
    "caption",
    "text",
    "名称",
    "单据名称",
    "单据类型",
    "业务名称",
    "业务类型",
)
PRODUCT_METADATA = {
    TCLOUD_PRODUCT_CODE: {
        "code": TCLOUD_PRODUCT_CODE,
        "name": "T+Cloud",
        "tool": "call_tplus_api",
        "aliases": ("tcloud", "tplus", "t+"),
    },
    HYC_PRODUCT_CODE: {
        "code": HYC_PRODUCT_CODE,
        "name": "HYC/ZPlus",
        "tool": "call_hyc_api",
        "aliases": ("hyc", "zplus"),
    },
    HSY_PRODUCT_CODE: {
        "code": HSY_PRODUCT_CODE,
        "name": "HSY/好生意",
        "tool": "call_hsy_api",
        "aliases": ("hsy", "haoshengyi", "好生意"),
    },
    YDZ_PRODUCT_CODE: {
        "code": YDZ_PRODUCT_CODE,
        "name": "YDZ/Finance",
        "tool": "call_ydz_api",
        "aliases": ("ydz", "finance"),
    },
    HKJ_PRODUCT_CODE: {
        "code": HKJ_PRODUCT_CODE,
        "name": "HKJ/Accounting",
        "tool": "call_hkj_api",
        "aliases": ("hkj", "accounting"),
    },
}
PRODUCT_ALIASES = {
    alias: product_code
    for product_code, metadata in PRODUCT_METADATA.items()
    for alias in metadata["aliases"]
}
API_NAME_KEYS = (
    "apiName",
    "name",
    "title",
    "caption",
    "interfaceName",
    "methodName",
)
API_PATH_KEYS = (
    "apiUrl",
    "apiPath",
    "path",
    "url",
    "requestUrl",
    "requestPath",
    "interfaceUrl",
    "address",
)
API_METHOD_KEYS = ("requestMethod", "httpMethod", "method")
API_BODY_KEYS = (
    "requestBody",
    "body",
    "requestJson",
    "requestExample",
    "requestData",
)
API_QUERY_KEYS = ("query", "queryParams", "requestQuery", "urlParams")
SMART_FIELD_NAME_KEYS = (
    "field",
    "fieldName",
    "FieldName",
    "name",
    "paramName",
    "parameterName",
    "code",
    "key",
    "property",
)
SMART_FIELD_LABEL_KEYS = (
    "label",
    "title",
    "caption",
    "Caption",
    "displayName",
    "paramDesc",
    "description",
    "desc",
    "name",
    "fieldLabel",
    "字段名称",
    "字段名",
    "名称",
    "中文名称",
)
SMART_FIELD_CHILD_KEYS = (
    "children",
    "items",
    "params",
    "parameters",
    "requestParams",
    "requestParameters",
    "fields",
    "columns",
    "properties",
)


class ChanjetApiError(RuntimeError):
    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        hint: str | None = None,
        trace_id: str | None = None,
    ):
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.trace_id = trace_id

    def to_dict(self) -> dict[str, str | None]:
        return {
            "code": self.code,
            "message": self.message,
            "hint": self.hint,
            "trace_id": self.trace_id,
        }


class ChanjetTCloudClient:
    def __init__(
        self,
        settings: ChanjetSettings | None = None,
        transport: JsonTransport | None = None,
        token_store: TokenStore | None = None,
    ):
        self.settings = settings or ChanjetSettings.from_env_file()
        self.transport = transport or UrlLibTransport(self.settings.timeout_seconds)
        self.token_store = token_store or TokenStore(self.settings.token_store_path)

    def list_modules(self, product_code: str) -> dict[str, Any]:
        if not product_code:
            raise ValueError("product_code is required")
        response = self.transport.request(
            "GET", self._docs_url("doc-center", "modulesNameByCode", product_code)
        )
        return self._unwrap_docs_response(response)

    def list_tcloud_modules(self) -> dict[str, Any]:
        return self.list_modules(TCLOUD_PRODUCT_CODE)

    def list_hyc_modules(self) -> dict[str, Any]:
        return self.list_modules(HYC_PRODUCT_CODE)

    def list_hsy_modules(self) -> dict[str, Any]:
        return self.list_modules(HSY_PRODUCT_CODE)

    def list_ydz_modules(self) -> dict[str, Any]:
        return self.list_modules(YDZ_PRODUCT_CODE)

    def list_hkj_modules(self) -> dict[str, Any]:
        return self.list_modules(HKJ_PRODUCT_CODE)

    def get_doc(
        self,
        product_code: str,
        parent_code: str,
        module_code: str,
        *,
        non_object_value: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not product_code:
            raise ValueError("product_code is required")
        if not parent_code or not module_code:
            raise ValueError("parent_code and module_code are required")
        response = self.transport.request(
            "GET",
            self._docs_url(
                "doc-center",
                "details",
                product_code,
                parent_code,
                module_code,
            ),
        )
        return self._unwrap_docs_response(response, non_object_value=non_object_value)

    def get_tcloud_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(TCLOUD_PRODUCT_CODE, parent_code, module_code)

    def get_hyc_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(HYC_PRODUCT_CODE, parent_code, module_code)

    def get_hsy_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(HSY_PRODUCT_CODE, parent_code, module_code)

    def get_ydz_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(YDZ_PRODUCT_CODE, parent_code, module_code)

    def get_hkj_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(HKJ_PRODUCT_CODE, parent_code, module_code)

    def search_docs(
        self,
        product_code: str,
        query: str,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if not product_code:
            raise ValueError("product_code is required")
        if not query:
            raise ValueError("query is required")
        normalized_query = query.casefold()
        matches: list[dict[str, Any]] = []

        module_tree = self.list_modules(product_code)
        for parent in module_tree.get("children") or []:
            parent_code = parent.get("moduleCode", "")
            parent_name = parent.get("moduleName", "")
            for child in parent.get("children") or []:
                module_code = child.get("moduleCode", "")
                module_name = child.get("moduleName", "")
                haystack = " ".join(
                    str(value)
                    for value in (parent_code, parent_name, module_code, module_name)
                    if value
                ).casefold()
                if normalized_query not in haystack:
                    continue
                matches.append(
                    {
                        "parent_code": parent_code,
                        "parent_name": parent_name,
                        "module_code": module_code,
                        "module_name": module_name,
                        "path": [product_code, parent_code, module_code],
                    }
                )
                if len(matches) >= limit:
                    return matches
        return matches

    def search_tcloud_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(TCLOUD_PRODUCT_CODE, query, limit)

    def search_hyc_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(HYC_PRODUCT_CODE, query, limit)

    def search_hsy_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(HSY_PRODUCT_CODE, query, limit)

    def search_ydz_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(YDZ_PRODUCT_CODE, query, limit)

    def search_hkj_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(HKJ_PRODUCT_CODE, query, limit)

    def get_tplus_reference_codes(self, query: str | None = None) -> dict[str, Any]:
        voucher_doc = self.get_tcloud_doc(
            TPLUS_DESCRIPTION_PARENT_CODE,
            TPLUS_VOUCHER_TYPE_MODULE_CODE,
        )
        business_doc = self.get_tcloud_doc(
            TPLUS_DESCRIPTION_PARENT_CODE,
            TPLUS_BUSINESS_TYPE_MODULE_CODE,
        )
        voucher_types = self._filter_reference_code_rows(
            self._extract_reference_code_rows(voucher_doc),
            query,
        )
        business_types = self._filter_reference_code_rows(
            self._extract_reference_code_rows(business_doc),
            query,
        )

        return {
            "voucher_types": voucher_types,
            "business_types": business_types,
            "source_docs": {
                "voucher_types": {
                    "product": TCLOUD_PRODUCT_CODE,
                    "parent_code": TPLUS_DESCRIPTION_PARENT_CODE,
                    "module_code": TPLUS_VOUCHER_TYPE_MODULE_CODE,
                },
                "business_types": {
                    "product": TCLOUD_PRODUCT_CODE,
                    "parent_code": TPLUS_DESCRIPTION_PARENT_CODE,
                    "module_code": TPLUS_BUSINESS_TYPE_MODULE_CODE,
                },
            },
        }

    def get_tplus_voucher_list_fields(
        self,
        *,
        biz_code: str,
        query: str | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        if not biz_code:
            raise ValueError("biz_code is required")

        request_body = self._voucher_field_request_body(biz_code)
        search_response = self.call_tplus_api(
            path=TPLUS_VOUCHER_SEARCH_ITEM_PATH,
            method="POST",
            body=request_body,
            headers=headers,
            account_alias=account_alias,
        )
        column_response = self.call_tplus_api(
            path=TPLUS_VOUCHER_COLUMN_SET_PATH,
            method="POST",
            body=request_body,
            headers=headers,
            account_alias=account_alias,
        )
        query_fields = self._filter_voucher_fields(
            self._extract_voucher_display_fields(search_response),
            query,
        )
        display_fields = self._filter_voucher_fields(
            self._extract_voucher_display_fields(column_response),
            query,
        )

        return {
            "biz_code": biz_code,
            "query_fields": query_fields,
            "display_fields": display_fields,
            "source_doc": {
                "product": TCLOUD_PRODUCT_CODE,
                "parent_code": TPLUS_VOUCHER_LIST_FIELD_DOC_PARENT_CODE,
                "module_code": TPLUS_VOUCHER_LIST_FIELD_DOC_MODULE_CODE,
            },
        }

    def diagnose_config(self, *, now: int | float | None = None) -> dict[str, Any]:
        current_time = int(now if now is not None else time.time())
        active_alias = self._resolve_account_alias(None, allow_legacy=False)
        account_summaries = self.token_store.list_account_summaries(
            active_alias=active_alias
        )
        active_summary = next(
            (
                account
                for account in account_summaries
                if account["account_alias"] == active_alias
            ),
            None,
        )
        legacy_open_token = bool(self.settings.open_token)
        legacy_refresh_token = bool(self.settings.refresh_token)
        active_expires_at = (
            active_summary.get("expires_at") if active_summary is not None else None
        )
        active_token_expired = self._expires_at_is_expired(
            active_expires_at,
            now=current_time,
        )
        has_active_open_token = bool(
            active_summary and active_summary.get("has_open_token")
        )
        has_active_refresh_token = bool(
            active_summary and active_summary.get("has_refresh_token")
        )
        if active_alias is None:
            has_active_open_token = legacy_open_token
            has_active_refresh_token = legacy_refresh_token

        has_app_key = bool(self.settings.app_key)
        has_app_secret = bool(self.settings.app_secret)
        has_redirect_uri = bool(self.settings.redirect_uri)
        if active_alias is None:
            has_any_token = legacy_open_token or legacy_refresh_token
        else:
            has_any_token = has_active_open_token or has_active_refresh_token
        business_api_calls = has_app_key and has_app_secret and has_any_token

        issues: list[dict[str, str]] = []
        if not has_app_key:
            issues.append(
                self._config_issue(
                    "missing_app_key",
                    "CHANJET_APP_KEY is not configured.",
                    "Set CHANJET_APP_KEY in the MCP client env or .env file.",
                )
            )
        if not has_app_secret:
            issues.append(
                self._config_issue(
                    "missing_app_secret",
                    "CHANJET_APP_SECRET is not configured.",
                    "Set CHANJET_APP_SECRET in the MCP client env or .env file.",
                )
            )
        if not has_redirect_uri:
            issues.append(
                self._config_issue(
                    "missing_redirect_uri",
                    "CHANJET_REDIRECT_URI is not configured.",
                    "Set CHANJET_REDIRECT_URI or pass redirect_uri to OAuth tools.",
                )
            )
        if active_alias and active_summary is None:
            issues.append(
                self._config_issue(
                    "unknown_active_account",
                    f"Active account '{active_alias}' does not exist in the token store.",
                    "Run oauth_complete_setup for this alias or set another active account.",
                )
            )
        if not has_any_token:
            issues.append(
                self._config_issue(
                    "missing_token",
                    "No open token or refresh token is available.",
                    "Run oauth_complete_setup or configure CHANJET_OPEN_TOKEN/CHANJET_REFRESH_TOKEN.",
                )
            )
        if active_token_expired and not has_active_refresh_token:
            issues.append(
                self._config_issue(
                    "expired_token_without_refresh",
                    "The active account open token is expired and no refresh token is available.",
                    "Re-authorize the account with oauth_complete_setup.",
                )
            )

        return {
            "settings": {
                "has_app_key": has_app_key,
                "has_app_secret": has_app_secret,
                "has_redirect_uri": has_redirect_uri,
                "token_store_path": self.settings.token_store_path,
                "base_url": self.settings.base_url,
                "docs_api_url": self.settings.docs_api_url,
                "timeout_seconds": self.settings.timeout_seconds,
            },
            "accounts": {
                "active_account": active_alias,
                "stored_account_count": len(account_summaries),
                "active_account_exists": active_summary is not None,
                "has_active_open_token": has_active_open_token,
                "has_active_refresh_token": has_active_refresh_token,
                "active_token_expired": active_token_expired,
                "uses_legacy_open_token": legacy_open_token and active_alias is None,
                "uses_legacy_refresh_token": legacy_refresh_token
                and active_alias is None,
            },
            "capabilities": {
                "documentation_lookup": True,
                "oauth_url_generation": has_app_key and has_redirect_uri,
                "token_exchange": has_app_key and has_redirect_uri,
                "business_api_calls": business_api_calls,
            },
            "issues": issues,
        }

    def get_api_call_template(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
    ) -> dict[str, Any]:
        metadata = self._product_metadata(product)
        doc = self.get_doc(
            metadata["code"],
            parent_code,
            module_code,
            non_object_value={},
        )
        requested_name = self._normalize_match_value(api_name) if api_name else ""
        templates = []
        for entry in self._extract_api_entries(doc):
            template = self._api_entry_to_template(entry, metadata)
            if requested_name:
                haystack = self._normalize_match_value(
                    " ".join(
                        str(value)
                        for value in (
                            template["api_name"],
                            template["path"],
                            template["method"],
                        )
                        if value
                    )
                )
                if requested_name not in haystack:
                    continue
            templates.append(template)

        return {
            "product": {
                "input": product,
                "code": metadata["code"],
                "name": metadata["name"],
                "tool": metadata["tool"],
            },
            "module": {
                "parent_code": parent_code,
                "module_code": module_code,
                "module_name": doc.get("moduleName"),
                "module_path": doc.get("modulePath"),
            },
            "templates": templates,
        }

    def search_api_templates(
        self,
        query: str,
        product: str | None = None,
        api_name: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        if not query:
            raise ValueError("query is required")
        product_metadatas = (
            [self._product_metadata(product)]
            if product
            else [dict(metadata) for metadata in PRODUCT_METADATA.values()]
        )
        templates: list[dict[str, Any]] = []

        for metadata in product_metadatas:
            if len(templates) >= limit:
                break
            remaining = max(limit - len(templates), 1)
            for module in self.search_docs(metadata["code"], query, limit=remaining):
                template_result = self.get_api_call_template(
                    product=metadata["code"],
                    parent_code=module["parent_code"],
                    module_code=module["module_code"],
                    api_name=api_name,
                )
                for template in template_result["templates"]:
                    enriched = copy.deepcopy(template)
                    enriched["product"] = template_result["product"]
                    enriched["module"] = template_result["module"]
                    templates.append(enriched)
                    if len(templates) >= limit:
                        break
                if len(templates) >= limit:
                    break

        return {
            "query": query,
            "product": product,
            "api_name": api_name,
            "templates": templates,
        }

    def call_api_template(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
    ) -> dict[str, Any]:
        template_result = self.get_api_call_template(
            product=product,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
        )
        if not template_result["templates"]:
            raise ValueError("No API template matched the requested module and api_name")

        template = template_result["templates"][0]
        request_args = copy.deepcopy(template["arguments"])
        if method is not None:
            request_args["method"] = method
        if body is not None:
            request_args["body"] = body
        if query is not None:
            request_args["query"] = query
        if headers is not None:
            request_args["headers"] = headers
        if account_alias is not None:
            request_args["account_alias"] = account_alias

        response = self._call_api_by_product(
            template_result["product"]["code"],
            path=request_args["path"],
            method=request_args["method"],
            body=request_args.get("body"),
            query=request_args.get("query"),
            headers=request_args.get("headers"),
            account_alias=request_args.get("account_alias"),
        )
        return {
            "template": template,
            "request": request_args,
            "data": response,
        }

    def call_api_smart(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        body_overrides: Any = None,
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
        template_result = self.get_api_call_template(
            product=product,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
        )
        if not template_result["templates"]:
            raise ValueError("No API template matched the requested module and api_name")

        template = template_result["templates"][0]
        request_args = copy.deepcopy(template["arguments"])
        if method is not None:
            request_args["method"] = method
        if query is not None:
            request_args["query"] = query
        if headers is not None:
            request_args["headers"] = headers
        if account_alias is not None:
            request_args["account_alias"] = account_alias

        body = copy.deepcopy(request_args.get("body"))
        matched_fields: list[dict[str, Any]] = []
        unmatched_fields: list[str] = []
        if fields:
            body, matched_fields, unmatched_fields = self._inject_smart_fields(
                body,
                fields,
                template,
            )
            if unmatched_fields:
                raise ValueError(
                    f"Unmatched smart fields: {', '.join(unmatched_fields)}"
                )

        tplus_resolved: dict[str, Any] = {}
        if template_result["product"]["code"] == TCLOUD_PRODUCT_CODE:
            body, tplus_resolved = self._apply_tplus_smart_fields(
                body=body,
                voucher_name=voucher_name,
                biz_code=biz_code,
                business_type_name=business_type_name,
                business_type=business_type,
                filters=filters,
                display_fields=display_fields,
                headers=headers,
                account_alias=account_alias,
            )

        if body_overrides is not None:
            body = self._deep_merge_values(body, body_overrides)
        request_args["body"] = body

        response = self._call_api_by_product(
            template_result["product"]["code"],
            path=request_args["path"],
            method=request_args["method"],
            body=request_args.get("body"),
            query=request_args.get("query"),
            headers=request_args.get("headers"),
            account_alias=request_args.get("account_alias"),
        )

        resolved = {
            "product_code": template_result["product"]["code"],
            "matched_fields": matched_fields,
            "unmatched_fields": unmatched_fields,
        }
        resolved.update(tplus_resolved)
        return {
            "template": template,
            "resolved": resolved,
            "request": request_args,
            "data": response,
        }

    def call_tplus_api_smart(
        self,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        voucher_name: str | None = None,
        biz_code: str | None = None,
        business_type_name: str | None = None,
        business_type: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        body_overrides: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
    ) -> dict[str, Any]:
        return self.call_api_smart(
            product=TCLOUD_PRODUCT_CODE,
            parent_code=parent_code,
            module_code=module_code,
            api_name=api_name,
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

    def safe_diagnose_config(self) -> dict[str, Any]:
        try:
            return self.tool_success(self.diagnose_config())
        except Exception as exc:
            return self.tool_error(exc)

    def safe_get_tplus_reference_codes(
        self,
        query: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(self.get_tplus_reference_codes(query=query))
        except Exception as exc:
            return self.tool_error(exc)

    def safe_get_tplus_voucher_list_fields(
        self,
        biz_code: str,
        query: str | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.get_tplus_voucher_list_fields(
                    biz_code=biz_code,
                    query=query,
                    headers=headers,
                    account_alias=account_alias,
                )
            )
        except Exception as exc:
            return self.tool_error(exc)

    def safe_get_api_call_template(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.get_api_call_template(
                    product=product,
                    parent_code=parent_code,
                    module_code=module_code,
                    api_name=api_name,
                )
            )
        except Exception as exc:
            return self.tool_error(
                exc,
                hint=(
                    "Use one of: tplus, tcloud, hyc, zplus, hsy, haoshengyi, "
                    "ydz, finance, hkj, accounting."
                ),
            )

    def safe_search_api_templates(
        self,
        query: str,
        product: str | None = None,
        api_name: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.search_api_templates(
                    query=query,
                    product=product,
                    api_name=api_name,
                    limit=limit,
                )
            )
        except Exception as exc:
            return self.tool_error(exc)

    def safe_call_api_template(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.call_api_template(
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
            )
        except Exception as exc:
            return self.tool_error(exc)

    def safe_call_api_smart(
        self,
        product: str,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        fields: dict[str, Any] | None = None,
        body_overrides: Any = None,
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
        try:
            return self.tool_success(
                self.call_api_smart(
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
            )
        except Exception as exc:
            return self.tool_error(
                exc,
                hint=(
                    "Use exact API field names or call get_api_call_template/"
                    "search_api_templates to inspect available fields."
                ),
            )

    def safe_call_tplus_api_smart(
        self,
        parent_code: str,
        module_code: str,
        api_name: str | None = None,
        *,
        voucher_name: str | None = None,
        biz_code: str | None = None,
        business_type_name: str | None = None,
        business_type: str | None = None,
        filters: dict[str, Any] | None = None,
        display_fields: list[str] | None = None,
        body_overrides: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
        method: str | None = None,
    ) -> dict[str, Any]:
        try:
            return self.tool_success(
                self.call_tplus_api_smart(
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
            )
        except Exception as exc:
            hint = None
            if "No API template matched" in str(exc):
                hint = (
                    "Use search_api_templates or get_api_call_template to verify "
                    "parent_code, module_code, and api_name before calling "
                    "call_tplus_api_smart."
                )
            return self.tool_error(
                exc,
                hint=hint,
            )

    def tool_success(self, data: Any) -> dict[str, Any]:
        return {"ok": True, "data": data}

    def tool_error(self, error: Exception, *, hint: str | None = None) -> dict[str, Any]:
        code = "internal_error"
        message = str(error) or error.__class__.__name__
        trace_id = None
        resolved_hint = hint

        if isinstance(error, ChanjetApiError):
            code = error.code or "chanjet_api_error"
            message = error.message
            resolved_hint = hint or error.hint
            trace_id = error.trace_id
        elif isinstance(error, ValueError):
            code = "invalid_argument"
        elif isinstance(error, HttpTransportError):
            code = "transport_error"

        return {
            "ok": False,
            "error": {
                "code": code,
                "message": message,
                "hint": resolved_hint,
                "trace_id": trace_id,
            },
        }

    def call_chanjet_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        if not path:
            raise ValueError("path is required")
        if path.startswith("http://") or path.startswith("https://"):
            raise ValueError("path must be a relative OpenAPI path")

        normalized_path = path if path.startswith("/") else f"/{path}"
        url = f"{self.settings.base_url}{normalized_path}"
        auth_headers, resolved_alias = self._openapi_headers_for_call(account_alias)
        merged_headers = dict(headers or {})
        merged_headers.update(auth_headers)

        response = self.transport.request(
            method.upper(),
            url,
            headers=merged_headers,
            params=query,
            json_body=body,
        )
        if not self._response_indicates_token_issue(response):
            return response

        refreshed_headers, _resolved_alias = self._openapi_headers_for_call(
            resolved_alias,
            force_refresh=True,
        )
        retry_headers = dict(headers or {})
        retry_headers.update(refreshed_headers)
        return self.transport.request(
            method.upper(),
            url,
            headers=retry_headers,
            params=query,
            json_body=body,
        )

    def call_tplus_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

    def query_tplus_voucher_list(
        self,
        *,
        biz_code: str,
        path: str,
        method: str = "POST",
        body: Any = None,
        display_fields: list[str] | None = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> dict[str, Any]:
        if not biz_code:
            raise ValueError("biz_code is required")
        if not path:
            raise ValueError("path is required")

        field_data = self.get_tplus_voucher_list_fields(
            biz_code=biz_code,
            headers=headers,
            account_alias=account_alias,
        )
        available_fields = field_data["display_fields"]
        matched_fields, unmatched_fields = self._match_display_fields(
            display_fields or [],
            available_fields,
        )
        list_body = self._inject_display_fields(
            body,
            [field["field"] for field in matched_fields],
        )
        list_response = self.call_tplus_api(
            path=path,
            method=method,
            body=list_body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

        return {
            "data": list_response,
            "query_fields": field_data["query_fields"],
            "display_fields": available_fields,
            "matched_display_fields": matched_fields,
            "unmatched_display_fields": unmatched_fields,
            "source_doc": field_data["source_doc"],
        }

    def call_hyc_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

    def call_hsy_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

    def call_ydz_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

    def call_hkj_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
            account_alias=account_alias,
        )

    def oauth_complete_setup(
        self,
        code: str,
        redirect_uri: str | None = None,
        account_alias: str | None = None,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
        now: int | float | None = None,
    ) -> dict[str, Any]:
        if not account_alias:
            raise ValueError("account_alias is required")
        token_response = self.exchange_token(
            code=code,
            redirect_uri=redirect_uri,
            timestamp=timestamp,
            nonce=nonce,
        )
        has_active = bool(
            self.settings.active_account or self.token_store.get_active_account_alias()
        )
        return self.token_store.save_token_response(
            account_alias,
            token_response,
            now=now,
            make_active=not has_active,
        )

    def list_auth_accounts(self) -> list[dict[str, Any]]:
        return self.token_store.list_account_summaries(
            active_alias=self._resolve_account_alias(None, allow_legacy=False)
        )

    def get_active_account(self) -> dict[str, Any] | None:
        alias = self._resolve_account_alias(None, allow_legacy=False)
        if not alias:
            return None
        summary = self.token_store.get_account_summary(alias, active_alias=alias)
        if summary is None:
            raise ValueError(f"Unknown Chanjet account alias: {alias}")
        return summary

    def set_active_account(self, account_alias: str) -> dict[str, Any]:
        return self.token_store.set_active_account(account_alias)

    def delete_auth_account(self, account_alias: str) -> dict[str, Any]:
        return self.token_store.delete_account(account_alias)

    def get_auth_url(
        self,
        redirect_uri: str | None = None,
        state: str | None = None,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> str:
        if not self.settings.app_key:
            raise ValueError("CHANJET_APP_KEY is required")
        resolved_redirect_uri = self._resolve_redirect_uri(redirect_uri)

        params = {
            "app_key": self.settings.app_key,
            "redirect_uri": resolved_redirect_uri,
            "response_type": "code",
            "state": state or uuid.uuid4().hex,
            "timestamp": timestamp or str(int(time.time())),
            "nonce": nonce or uuid.uuid4().hex,
        }
        params["sign"] = self._signature(params)
        return f"{self.settings.base_url}/oauth/authorize?{urlencode(params)}"

    def exchange_token(
        self,
        code: str,
        redirect_uri: str | None = None,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        if not code:
            raise ValueError("code is required")
        resolved_redirect_uri = self._resolve_redirect_uri(redirect_uri)
        params = self._token_params(
            grant_type="authorization_code",
            timestamp=timestamp,
            nonce=nonce,
        )
        params["code"] = code
        params["redirect_uri"] = resolved_redirect_uri
        params["sign"] = self._signature(params)
        response = self.transport.request(
            "GET", f"{self.settings.base_url}/auth/token", params=params
        )
        return self._normalize_token_response(response)

    def _resolve_redirect_uri(self, redirect_uri: str | None) -> str:
        resolved_redirect_uri = redirect_uri or self.settings.redirect_uri
        if not resolved_redirect_uri:
            raise ValueError("redirect_uri is required")
        return resolved_redirect_uri

    def refresh_token(
        self,
        refresh_token: str | None = None,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        token = refresh_token or self.settings.refresh_token
        if not token:
            raise ValueError("refresh_token or CHANJET_REFRESH_TOKEN is required")
        params = self._token_params(
            grant_type="refresh_token",
            timestamp=timestamp,
            nonce=nonce,
        )
        params["refresh_token"] = token
        params["sign"] = self._signature(params)
        response = self.transport.request(
            "GET", f"{self.settings.base_url}/auth/token", params=params
        )
        return self._normalize_token_response(response)

    def _call_api_by_product(
        self,
        product_code: str,
        *,
        path: str,
        method: str,
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
        account_alias: str | None = None,
    ) -> Any:
        if product_code == TCLOUD_PRODUCT_CODE:
            return self.call_tplus_api(
                path=path,
                method=method,
                body=body,
                query=query,
                headers=headers,
                account_alias=account_alias,
            )
        if product_code == HYC_PRODUCT_CODE:
            return self.call_hyc_api(
                path=path,
                method=method,
                body=body,
                query=query,
                headers=headers,
                account_alias=account_alias,
            )
        if product_code == HSY_PRODUCT_CODE:
            return self.call_hsy_api(
                path=path,
                method=method,
                body=body,
                query=query,
                headers=headers,
                account_alias=account_alias,
            )
        if product_code == YDZ_PRODUCT_CODE:
            return self.call_ydz_api(
                path=path,
                method=method,
                body=body,
                query=query,
                headers=headers,
                account_alias=account_alias,
            )
        if product_code == HKJ_PRODUCT_CODE:
            return self.call_hkj_api(
                path=path,
                method=method,
                body=body,
                query=query,
                headers=headers,
                account_alias=account_alias,
            )
        raise ValueError(f"Unsupported product code: {product_code}")

    def _resolve_reference_code(
        self,
        rows: list[dict[str, Any]],
        query: str,
        *,
        label: str,
    ) -> str:
        matches = self._filter_reference_code_rows(rows, query)
        if not matches:
            raise ValueError(f"Could not resolve {label}: {query}")

        normalized_query = self._normalize_match_value(query)
        exact_matches = [
            row
            for row in matches
            if normalized_query
            in {
                self._normalize_match_value(row.get("code")),
                self._normalize_match_value(row.get("name")),
            }
        ]
        if len(exact_matches) == 1:
            return str(exact_matches[0]["code"])
        if len(matches) == 1:
            return str(matches[0]["code"])

        candidates = ", ".join(
            f"{row.get('name')}={row.get('code')}" for row in matches[:5]
        )
        raise ValueError(f"Ambiguous {label}: {query}. Candidates: {candidates}")

    def _ensure_param_body(self, body: Any) -> dict[str, Any]:
        if body is None:
            body = {}
        if not isinstance(body, dict):
            raise ValueError("Request body must be an object to inject smart fields")
        copied_body = copy.deepcopy(body)
        param = copied_body.get("param")
        if param is None:
            param = {}
            copied_body["param"] = param
        if not isinstance(param, dict):
            raise ValueError("Request body param must be an object to inject smart fields")
        return copied_body

    def _deep_merge_values(self, base: Any, override: Any) -> Any:
        if isinstance(base, dict) and isinstance(override, dict):
            merged = copy.deepcopy(base)
            for key, value in override.items():
                if key in merged:
                    merged[key] = self._deep_merge_values(merged[key], value)
                else:
                    merged[key] = copy.deepcopy(value)
            return merged
        return copy.deepcopy(override)

    def _apply_tplus_smart_fields(
        self,
        *,
        body: Any,
        voucher_name: str | None,
        biz_code: str | None,
        business_type_name: str | None,
        business_type: str | None,
        filters: dict[str, Any] | None,
        display_fields: list[str] | None,
        headers: dict[str, str] | None,
        account_alias: str | None,
    ) -> tuple[Any, dict[str, Any]]:
        resolved_biz_code = biz_code
        resolved_business_type = business_type
        reference_lookup: dict[str, Any] | None = None

        if voucher_name or business_type_name:
            reference_lookup = self.get_tplus_reference_codes()
        if not resolved_biz_code and voucher_name and reference_lookup is not None:
            resolved_biz_code = self._resolve_reference_code(
                reference_lookup["voucher_types"],
                voucher_name,
                label="voucher type",
            )
        if (
            not resolved_business_type
            and business_type_name
            and reference_lookup is not None
        ):
            resolved_business_type = self._resolve_reference_code(
                reference_lookup["business_types"],
                business_type_name,
                label="business type",
            )

        field_lookup: dict[str, Any] | None = None
        if filters or display_fields:
            if not resolved_biz_code:
                raise ValueError(
                    "biz_code or voucher_name is required to resolve filters or display_fields"
                )
            field_lookup = self.get_tplus_voucher_list_fields(
                biz_code=resolved_biz_code,
                headers=headers,
                account_alias=account_alias,
            )

        matched_filter_fields: list[dict[str, str]] = []
        matched_display_fields: list[dict[str, str]] = []
        if filters:
            body = self._ensure_param_body(body)
            param = body["param"]
            unmatched_filters: list[str] = []
            for requested, value in filters.items():
                requested_text = str(requested).strip()
                match = self._find_display_field_match(
                    requested_text,
                    field_lookup["query_fields"] if field_lookup else [],
                )
                if match is None:
                    unmatched_filters.append(requested_text)
                    continue
                field_name = str(match["field"])
                param[field_name] = value
                matched_filter_fields.append(
                    {
                        "requested": requested_text,
                        "field": field_name,
                        "label": str(match["label"]),
                    }
                )
            if unmatched_filters:
                raise ValueError(
                    f"Unmatched filter fields: {', '.join(unmatched_filters)}"
                )

        if resolved_business_type:
            body = self._ensure_param_body(body)
            body["param"]["BusinessType"] = resolved_business_type

        if display_fields:
            matched_display_fields, unmatched_display_fields = self._match_display_fields(
                display_fields,
                field_lookup["display_fields"] if field_lookup else [],
            )
            if unmatched_display_fields:
                raise ValueError(
                    f"Unmatched display fields: {', '.join(unmatched_display_fields)}"
                )
            body = self._inject_display_fields(
                body,
                [field["field"] for field in matched_display_fields],
            )

        return body, {
            "biz_code": resolved_biz_code,
            "voucher_name": voucher_name,
            "business_type": resolved_business_type,
            "business_type_name": business_type_name,
            "matched_filter_fields": matched_filter_fields,
            "matched_display_fields": matched_display_fields,
            "reference_source_docs": (
                reference_lookup.get("source_docs") if reference_lookup else None
            ),
            "field_source_doc": (
                field_lookup.get("source_doc") if field_lookup else None
            ),
        }

    def _inject_smart_fields(
        self,
        body: Any,
        fields: dict[str, Any],
        template: dict[str, Any],
    ) -> tuple[Any, list[dict[str, Any]], list[str]]:
        if body is None:
            body = {}
        updated_body = copy.deepcopy(body)
        path_prefix: list[Any] = []
        if isinstance(updated_body, dict):
            injection_body = updated_body
        elif isinstance(updated_body, list):
            if not updated_body:
                updated_body.append({})
            if not isinstance(updated_body[0], dict):
                raise ValueError(
                    "Request body array first item must be an object to inject smart fields"
                )
            injection_body = updated_body[0]
            path_prefix = [0]
        else:
            raise ValueError(
                "Request body must be an object or object array to inject smart fields"
            )
        aliases = self._smart_field_aliases(template)
        matched_fields: list[dict[str, Any]] = []
        unmatched_fields: list[str] = []

        for requested, value in fields.items():
            requested_text = str(requested).strip()
            normalized = self._normalize_match_value(requested_text)
            match = aliases.get(normalized)
            if match is None:
                unmatched_fields.append(requested_text)
                continue
            self._set_body_path(injection_body, match["path"], value)
            matched_fields.append(
                {
                    "requested": requested_text,
                    "field": match["field"],
                    "path": [*path_prefix, *match["path"]],
                }
            )

        return updated_body, matched_fields, unmatched_fields

    def _smart_field_aliases(self, template: dict[str, Any]) -> dict[str, dict[str, Any]]:
        aliases: dict[str, dict[str, Any]] = {}

        def register(path: list[str], field: str, labels: list[Any]) -> None:
            if not path or not field:
                return
            match = {"field": field, "path": path}
            for label in [field, *labels]:
                normalized = self._normalize_match_value(label)
                if normalized and normalized not in aliases:
                    aliases[normalized] = match

        def collect(item: Any, current_path: list[str] | None = None) -> None:
            current_path = current_path or []
            if isinstance(item, list):
                for child in item:
                    collect(child, current_path)
                return
            if not isinstance(item, dict):
                return

            field = self._first_mapping_value(item, SMART_FIELD_NAME_KEYS)
            labels = [
                value
                for key in SMART_FIELD_LABEL_KEYS
                for value in [item.get(key)]
                if value is not None
            ]
            if field is not None:
                field_text = str(field).strip()
                path = [*current_path, field_text] if current_path else [field_text]
                register(path, field_text, labels)

            for key, value in item.items():
                if key in SMART_FIELD_CHILD_KEYS:
                    collect(value, current_path)
                elif isinstance(value, dict):
                    collect(value, current_path)
                elif isinstance(value, list):
                    collect(value, current_path)

        collect(template.get("raw", template))
        body = template.get("body")
        if isinstance(body, dict):
            default_parent = ["param"] if isinstance(body.get("param"), dict) else []
            for key in body.get("param", body).keys():
                field_path = [*default_parent, str(key)]
                register(field_path, str(key), [])
        elif (
            isinstance(body, list)
            and body
            and isinstance(body[0], dict)
        ):
            for key in body[0].keys():
                register([str(key)], str(key), [])
        return aliases

    def _set_body_path(
        self,
        body: dict[str, Any],
        path: list[str],
        value: Any,
    ) -> None:
        target = body
        for key in path[:-1]:
            next_value = target.get(key)
            if not isinstance(next_value, dict):
                next_value = {}
                target[key] = next_value
            target = next_value
        target[path[-1]] = value

    def _config_issue(self, code: str, message: str, hint: str) -> dict[str, str]:
        return {"code": code, "message": message, "hint": hint}

    def _expires_at_is_expired(
        self,
        expires_at: Any,
        *,
        now: int | float,
    ) -> bool | None:
        if expires_at is None:
            return None
        try:
            return int(now) >= int(expires_at)
        except (TypeError, ValueError):
            return True

    def _product_metadata(self, product: str) -> dict[str, Any]:
        if not product:
            raise ValueError("product is required")
        product_key = str(product).strip().casefold()
        product_code = PRODUCT_ALIASES.get(product_key)
        if product_code is None:
            raise ValueError(f"Unsupported product: {product}")
        return dict(PRODUCT_METADATA[product_code])

    def _extract_api_entries(self, value: Any) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def collect(item: Any) -> None:
            if isinstance(item, list):
                for child in item:
                    collect(child)
                return
            if not isinstance(item, dict):
                return

            path = self._normalize_api_path(
                self._first_mapping_value(item, API_PATH_KEYS)
            )
            if path:
                name = self._first_mapping_value(item, API_NAME_KEYS) or path
                key = (path, str(name))
                if key not in seen:
                    seen.add(key)
                    entries.append(item)

            for child in item.values():
                if isinstance(child, (dict, list)):
                    collect(child)

        collect(value)
        return entries

    def _api_entry_to_template(
        self,
        entry: dict[str, Any],
        product_metadata: dict[str, Any],
    ) -> dict[str, Any]:
        path = self._normalize_api_path(
            self._first_mapping_value(entry, API_PATH_KEYS)
        )
        if not path:
            raise ValueError("API document entry does not include a callable path")

        api_name = self._first_mapping_value(entry, API_NAME_KEYS) or path
        method = str(
            self._first_mapping_value(entry, API_METHOD_KEYS) or "POST"
        ).upper()
        body = self._first_mapping_value(entry, API_BODY_KEYS)
        query = self._first_mapping_value(entry, API_QUERY_KEYS)
        headers = self._first_mapping_value(entry, ("headers", "requestHeaders"))

        if body is None:
            body = {}
        if not isinstance(query, dict):
            query = {}
        if not isinstance(headers, dict):
            headers = {}

        arguments = {
            "path": path,
            "method": method,
            "body": copy.deepcopy(body),
            "query": copy.deepcopy(query),
            "headers": copy.deepcopy(headers),
            "account_alias": None,
        }
        return {
            "api_name": str(api_name),
            "path": path,
            "method": method,
            "body": copy.deepcopy(body),
            "query": copy.deepcopy(query),
            "headers": copy.deepcopy(headers),
            "tool": product_metadata["tool"],
            "arguments": arguments,
            "raw": copy.deepcopy(entry),
        }

    def _normalize_api_path(self, value: Any) -> str | None:
        if value is None:
            return None
        path = str(value).strip()
        if not path:
            return None
        if "://" in path:
            parts = path.split("/", 3)
            if len(parts) < 4:
                return None
            path = f"/{parts[3]}"
        if not path.startswith("/"):
            path = f"/{path}"
        return path

    def _token_params(
        self,
        *,
        grant_type: str,
        timestamp: str | None,
        nonce: str | None,
    ) -> dict[str, str]:
        if not self.settings.app_key:
            raise ValueError("CHANJET_APP_KEY is required")
        return {
            "app_key": self.settings.app_key,
            "grant_type": grant_type,
            "timestamp": timestamp or str(int(time.time()) + 300),
            "nonce": nonce or uuid.uuid4().hex,
        }

    def _openapi_headers_for_call(
        self,
        account_alias: str | None,
        *,
        force_refresh: bool = False,
    ) -> tuple[dict[str, str], str | None]:
        alias = self._resolve_account_alias(account_alias)
        if alias:
            account = self.token_store.get_account(alias)
            if account is None:
                raise ValueError(f"Unknown Chanjet account alias: {alias}")
            if force_refresh or self._account_needs_refresh(account):
                account = self._refresh_stored_account(alias, account)
            open_token = account.get("open_token")
            if not open_token:
                raise ValueError(
                    f"Chanjet account '{alias}' has no open token and cannot be used"
                )
            return self.settings.openapi_headers(str(open_token)), alias

        if force_refresh and self.settings.refresh_token:
            self._refresh_legacy_settings_token()
        elif not self.settings.open_token and self.settings.refresh_token:
            self._refresh_legacy_settings_token()

        if self.settings.open_token:
            return self.settings.openapi_headers(), None

        raise ValueError(
            "No Chanjet account token is available; run oauth_complete_setup or pass account_alias"
        )

    def _resolve_account_alias(
        self,
        account_alias: str | None,
        *,
        allow_legacy: bool = True,
    ) -> str | None:
        if account_alias:
            return account_alias
        active_alias = self.token_store.get_active_account_alias()
        if active_alias:
            return active_alias
        if self.settings.active_account:
            return self.settings.active_account
        if allow_legacy:
            return None
        return None

    def _account_needs_refresh(self, account: dict[str, Any]) -> bool:
        if not account.get("open_token"):
            return True
        expires_at = account.get("expires_at")
        if expires_at is None:
            return False
        try:
            return time.time() >= int(expires_at)
        except (TypeError, ValueError):
            return True

    def _refresh_stored_account(
        self,
        account_alias: str,
        account: dict[str, Any],
    ) -> dict[str, Any]:
        refresh_token = account.get("refresh_token")
        if not refresh_token:
            raise ValueError(
                f"Chanjet account '{account_alias}' has no refresh token for automatic refresh"
            )
        token_response = self.refresh_token(refresh_token=str(refresh_token))
        self.token_store.save_token_response(account_alias, token_response)
        refreshed = self.token_store.get_account(account_alias)
        if refreshed is None:
            raise ValueError(f"Unknown Chanjet account alias: {account_alias}")
        return refreshed

    def _refresh_legacy_settings_token(self) -> None:
        if not self.settings.refresh_token:
            raise ValueError("CHANJET_REFRESH_TOKEN is required for automatic refresh")
        token_response = self.refresh_token(refresh_token=self.settings.refresh_token)
        self.settings = replace(
            self.settings,
            open_token=token_response["access_token"],
            refresh_token=token_response.get("refresh_token")
            or self.settings.refresh_token,
        )

    def _response_indicates_token_issue(self, response: Any) -> bool:
        if not self._response_looks_failed(response):
            return False

        values: list[str] = []

        def collect(value: Any) -> None:
            if isinstance(value, dict):
                for item in value.values():
                    collect(item)
            elif isinstance(value, list):
                for item in value:
                    collect(item)
            elif value is not None:
                values.append(str(value))

        collect(response)
        text = " ".join(values).casefold()
        if "token" not in text:
            return False
        return any(
            marker in text
            for marker in (
                "expired",
                "expire",
                "invalid",
                "unauthorized",
                "not valid",
                "过期",
                "失效",
                "无效",
            )
        )

    def _response_looks_failed(self, response: Any) -> bool:
        if not isinstance(response, dict):
            return False
        if response.get("error"):
            return True
        if response.get("result") is False or response.get("success") is False:
            return True

        code = response.get("code") or response.get("status")
        if code is None:
            return False
        normalized_code = str(code).casefold()
        return normalized_code not in {"0", "200", "openapi.e0000"}

    def _voucher_field_request_body(self, biz_code: str) -> dict[str, Any]:
        return {
            "bizCode": biz_code,
            "apiParam": {"dataSource": "openapi"},
        }

    def _voucher_column_request_body(self, biz_code: str) -> dict[str, Any]:
        return self._voucher_field_request_body(biz_code)

    def _extract_reference_code_rows(self, value: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def add_candidate(candidate: dict[str, Any]) -> None:
            normalized = self._normalize_reference_code_row(candidate)
            if normalized is None:
                return
            dedupe_key = (
                self._normalize_match_value(normalized["code"]),
                self._normalize_match_value(normalized["name"]),
            )
            if dedupe_key in seen:
                return
            seen.add(dedupe_key)
            rows.append(normalized)

        def collect(item: Any, *, list_item: bool = False) -> None:
            if isinstance(item, str):
                for parsed_row in self._extract_reference_rows_from_text(item):
                    add_candidate(parsed_row)
                return
            if isinstance(item, list):
                for child in item:
                    collect(child, list_item=True)
                return
            if not isinstance(item, dict):
                return

            if list_item or self._first_mapping_value(item, REFERENCE_CODE_KEYS):
                add_candidate(item)

            for child in item.values():
                if isinstance(child, (dict, list, str)):
                    collect(child)

        collect(value)
        return rows

    def _normalize_reference_code_row(
        self,
        value: dict[str, Any],
    ) -> dict[str, Any] | None:
        code = self._first_mapping_value(value, REFERENCE_CODE_KEYS)
        name = self._first_mapping_value(value, REFERENCE_NAME_KEYS)
        if code is None or name is None:
            return None

        code_text = str(code).strip()
        name_text = str(name).strip()
        if not code_text or not name_text:
            return None
        if self._normalize_match_value(code_text) == self._normalize_match_value(
            name_text
        ):
            return None

        return {
            "code": code_text,
            "name": name_text,
            "raw": value,
        }

    def _extract_reference_rows_from_text(self, text: str) -> list[dict[str, str]]:
        rows: list[dict[str, str]] = []
        for line in text.splitlines():
            cells = self._table_cells_from_text_line(line)
            if len(cells) < 2 or self._looks_like_table_header(cells):
                continue

            first, second = cells[0], cells[1]
            if self._looks_like_reference_code(first):
                code, name = first, second
            elif self._looks_like_reference_code(second):
                code, name = second, first
            else:
                code, name = first, second
            rows.append({"code": code, "name": name})
        return rows

    def _table_cells_from_text_line(self, line: str) -> list[str]:
        cleaned = line.strip()
        if not cleaned:
            return []
        if "<td" in cleaned.casefold():
            parts = cleaned.replace("</td>", "|").replace("</th>", "|")
            for marker in ("<tr>", "</tr>", "<tbody>", "</tbody>"):
                parts = parts.replace(marker, "")
            cells = []
            for part in parts.split("|"):
                text = part.split(">", 1)[-1].strip()
                if text:
                    cells.append(text)
            return cells
        if "|" not in cleaned:
            return []
        return [cell.strip() for cell in cleaned.strip("|").split("|") if cell.strip()]

    def _looks_like_table_header(self, cells: list[str]) -> bool:
        normalized_cells = [self._normalize_match_value(cell) for cell in cells]
        if all(set(cell) <= {"-"} for cell in cells):
            return True
        if not any(self._looks_like_reference_code(cell) for cell in cells):
            header_markers = (
                "code",
                "name",
                "bizcode",
                "businesstype",
                "编码",
                "名称",
                "类型",
            )
            if any(
                marker in cell
                for cell in normalized_cells
                for marker in header_markers
            ):
                return True
        return any(
            cell in {"code", "编码", "name", "名称", "businesstype", "bizcode"}
            for cell in normalized_cells
        )

    def _looks_like_reference_code(self, value: str) -> bool:
        text = value.strip()
        if not text:
            return False
        return all(ord(char) < 128 for char in text) and any(
            char.isdigit() for char in text
        )

    def _filter_reference_code_rows(
        self,
        rows: list[dict[str, Any]],
        query: str | None,
    ) -> list[dict[str, Any]]:
        normalized_query = self._normalize_match_value(query or "")
        if not normalized_query:
            return rows
        return [
            row
            for row in rows
            if any(
                normalized_query in self._normalize_match_value(value)
                for value in (row.get("code"), row.get("name"), row.get("raw"))
            )
        ]

    def _extract_voucher_display_fields(self, response: Any) -> list[dict[str, Any]]:
        display_fields: list[dict[str, Any]] = []
        seen: set[tuple[str, str]] = set()

        def add_candidate(value: Any) -> None:
            normalized = self._normalize_display_field(value)
            if normalized is None:
                return
            dedupe_key = (
                self._normalize_match_value(normalized["field"]),
                self._normalize_match_value(normalized["label"]),
            )
            if dedupe_key in seen:
                return
            seen.add(dedupe_key)
            display_fields.append(normalized)

        def collect(value: Any, *, list_item: bool = False) -> None:
            if isinstance(value, list):
                for item in value:
                    collect(item, list_item=True)
                return
            if not isinstance(value, dict):
                return

            if list_item:
                add_candidate(value)

            for item in value.values():
                if isinstance(item, (dict, list)):
                    collect(item)

        collect(response)
        return display_fields

    def _filter_voucher_fields(
        self,
        fields: list[dict[str, Any]],
        query: str | None,
    ) -> list[dict[str, Any]]:
        normalized_query = self._normalize_match_value(query or "")
        if not normalized_query:
            return fields

        filtered: list[dict[str, Any]] = []
        for field in fields:
            values = self._display_field_match_values(field)
            raw_value = self._normalize_match_value(field.get("raw"))
            if normalized_query in raw_value or any(
                normalized_query in value or value in normalized_query
                for value in values
            ):
                filtered.append(field)
        return filtered

    def _normalize_display_field(self, value: Any) -> dict[str, Any] | None:
        if not isinstance(value, dict):
            return None

        field = self._first_mapping_value(
            value,
            (
                "field",
                "fieldName",
                "fieldCode",
                "columnName",
                "propertyName",
                "dataIndex",
                "code",
                "key",
                "id",
            ),
        )
        label = self._first_mapping_value(
            value,
            (
                "caption",
                "title",
                "label",
                "displayName",
                "fieldCaption",
                "text",
                "header",
                "name",
            ),
        )
        if field is None and label is None:
            return None

        field_text = str(field if field is not None else label).strip()
        label_text = str(label if label is not None else field).strip()
        if not field_text and not label_text:
            return None

        normalized: dict[str, Any] = {
            "field": field_text,
            "label": label_text,
            "raw": value,
        }
        for output_key, source_keys in (
            ("name", ("name",)),
            ("title", ("title",)),
            ("caption", ("caption",)),
            ("code", ("code",)),
            ("key", ("key",)),
        ):
            source_value = self._first_mapping_value(value, source_keys)
            if source_value is not None:
                normalized[output_key] = str(source_value).strip()
        return normalized

    def _match_display_fields(
        self,
        requested_fields: list[str],
        available_fields: list[dict[str, Any]],
    ) -> tuple[list[dict[str, str]], list[str]]:
        matched: list[dict[str, str]] = []
        unmatched: list[str] = []

        for requested in requested_fields:
            requested_text = str(requested).strip()
            if not requested_text:
                continue
            match = self._find_display_field_match(requested_text, available_fields)
            if match is None:
                unmatched.append(requested_text)
                continue
            matched.append(
                {
                    "requested": requested_text,
                    "field": str(match["field"]),
                    "label": str(match["label"]),
                }
            )

        return matched, unmatched

    def _find_display_field_match(
        self,
        requested: str,
        available_fields: list[dict[str, Any]],
    ) -> dict[str, Any] | None:
        requested_key = self._normalize_match_value(requested)
        if not requested_key:
            return None

        field_values = [
            (field, self._display_field_match_values(field))
            for field in available_fields
        ]
        for field, values in field_values:
            if requested_key in values:
                return field
        for field, values in field_values:
            if any(requested_key in value or value in requested_key for value in values):
                return field
        return None

    def _display_field_match_values(self, field: dict[str, Any]) -> set[str]:
        values: set[str] = set()
        for key in ("field", "label", "name", "title", "caption", "code", "key"):
            value = field.get(key)
            if value is None:
                continue
            normalized = self._normalize_match_value(value)
            if normalized:
                values.add(normalized)
        return values

    def _inject_display_fields(self, body: Any, fields: list[str]) -> Any:
        copied_body = copy.deepcopy(body)
        if not fields:
            return copied_body

        if copied_body is None:
            copied_body = {}
        if not isinstance(copied_body, dict):
            return copied_body
        if self._has_existing_field_selection(copied_body):
            return copied_body

        param = copied_body.get("param")
        if param is None:
            param = {}
            copied_body["param"] = param
        if not isinstance(param, dict):
            return copied_body
        param["selectFields"] = fields
        return copied_body

    def _has_existing_field_selection(self, value: Any) -> bool:
        if isinstance(value, dict):
            for key, item in value.items():
                if str(key).casefold() in VOUCHER_FIELD_SELECTION_KEYS:
                    return True
                if self._has_existing_field_selection(item):
                    return True
        elif isinstance(value, list):
            return any(self._has_existing_field_selection(item) for item in value)
        return False

    def _first_mapping_value(
        self,
        value: dict[str, Any],
        keys: tuple[str, ...],
    ) -> Any:
        normalized_keys = {str(key).casefold(): item for key, item in value.items()}
        for key in keys:
            item = normalized_keys.get(key.casefold())
            if item is not None and str(item).strip():
                return item
        return None

    def _normalize_match_value(self, value: Any) -> str:
        return "".join(char for char in str(value).casefold() if char.isalnum())

    def _docs_url(self, *parts: str) -> str:
        encoded_parts = [quote(str(part), safe="") for part in parts]
        return f"{self.settings.docs_api_url}/{'/'.join(encoded_parts)}"

    def _unwrap_docs_response(
        self,
        response: Any,
        *,
        non_object_value: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not isinstance(response, dict):
            raise ChanjetApiError("Unexpected Chanjet document API response")
        if response.get("result") is True:
            value = response.get("value")
            if isinstance(value, dict):
                return value
            if non_object_value is not None:
                return copy.deepcopy(non_object_value)
            raise ChanjetApiError("Chanjet document API returned a non-object value")

        error = response.get("error") or {}
        message = (
            error.get("msg")
            or error.get("message")
            or error.get("hint")
            or "Chanjet document API request failed"
        )
        raise ChanjetApiError(
            message,
            code=str(error.get("code")) if error.get("code") is not None else None,
            hint=error.get("hint"),
            trace_id=response.get("traceId"),
        )

    def _normalize_token_response(self, response: Any) -> dict[str, Any]:
        if not isinstance(response, dict):
            raise ChanjetApiError("Unexpected Chanjet token API response")

        if response.get("error"):
            raise ChanjetApiError(str(response.get("error")))

        code = response.get("code")
        if code is not None and str(code) != "200":
            raise ChanjetApiError(
                response.get("message")
                or response.get("error_description")
                or "Chanjet token API request failed",
                code=str(code),
            )

        raw = response.get("result", response)
        if not isinstance(raw, dict):
            raise ChanjetApiError("Chanjet token API returned a non-object value")

        access_token = raw.get("accessToken") or raw.get("access_token")
        if not access_token:
            raise ChanjetApiError("Chanjet token API response did not include access_token")

        return {
            "access_token": access_token,
            "refresh_token": raw.get("refreshToken") or raw.get("refresh_token"),
            "expires_in": raw.get("expiresIn") or raw.get("expires_in"),
            "raw": raw,
        }

    def _signature(self, params: dict[str, Any]) -> str:
        sign_string = "&".join(
            f"{key}={value}"
            for key, value in sorted(params.items())
            if value is not None and value != ""
        )
        return hashlib.md5(sign_string.encode("utf-8")).hexdigest().upper()
