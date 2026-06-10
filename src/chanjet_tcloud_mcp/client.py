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
from .transport import JsonTransport, UrlLibTransport


TCLOUD_PRODUCT_CODE = "tcloud"
HYC_PRODUCT_CODE = "zplus"
YDZ_PRODUCT_CODE = "finance"
HKJ_PRODUCT_CODE = "accounting"
TPLUS_VOUCHER_COLUMN_SET_PATH = (
    "/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode"
)
VOUCHER_FIELD_SELECTION_KEYS = {"selectfields", "fields", "columns", "select"}


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

    def list_ydz_modules(self) -> dict[str, Any]:
        return self.list_modules(YDZ_PRODUCT_CODE)

    def list_hkj_modules(self) -> dict[str, Any]:
        return self.list_modules(HKJ_PRODUCT_CODE)

    def get_doc(
        self,
        product_code: str,
        parent_code: str,
        module_code: str,
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
        return self._unwrap_docs_response(response)

    def get_tcloud_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(TCLOUD_PRODUCT_CODE, parent_code, module_code)

    def get_hyc_doc(self, parent_code: str, module_code: str) -> dict[str, Any]:
        return self.get_doc(HYC_PRODUCT_CODE, parent_code, module_code)

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

    def search_ydz_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(YDZ_PRODUCT_CODE, query, limit)

    def search_hkj_docs(self, query: str, limit: int = 20) -> list[dict[str, Any]]:
        return self.search_docs(HKJ_PRODUCT_CODE, query, limit)

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

        column_response = self.call_tplus_api(
            path=TPLUS_VOUCHER_COLUMN_SET_PATH,
            method="POST",
            body=self._voucher_column_request_body(biz_code),
            headers=headers,
            account_alias=account_alias,
        )
        available_fields = self._extract_voucher_display_fields(column_response)
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
            "display_fields": available_fields,
            "matched_display_fields": matched_fields,
            "unmatched_display_fields": unmatched_fields,
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

    def _voucher_column_request_body(self, biz_code: str) -> dict[str, Any]:
        return {
            "bizCode": biz_code,
            "apiParam": {"dataSource": "openapi"},
        }

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

    def _unwrap_docs_response(self, response: Any) -> dict[str, Any]:
        if not isinstance(response, dict):
            raise ChanjetApiError("Unexpected Chanjet document API response")
        if response.get("result") is True:
            value = response.get("value")
            if isinstance(value, dict):
                return value
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
