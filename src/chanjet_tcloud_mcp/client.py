from __future__ import annotations

import hashlib
import time
import uuid
from typing import Any
from urllib.parse import quote, urlencode

from .settings import ChanjetSettings
from .transport import JsonTransport, UrlLibTransport


TCLOUD_PRODUCT_CODE = "tcloud"
HYC_PRODUCT_CODE = "zplus"
YDZ_PRODUCT_CODE = "finance"
HKJ_PRODUCT_CODE = "accounting"


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
    ):
        self.settings = settings or ChanjetSettings.from_env_file()
        self.transport = transport or UrlLibTransport(self.settings.timeout_seconds)

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
    ) -> Any:
        if not path:
            raise ValueError("path is required")
        if path.startswith("http://") or path.startswith("https://"):
            raise ValueError("path must be a relative OpenAPI path")

        normalized_path = path if path.startswith("/") else f"/{path}"
        merged_headers = dict(headers or {})
        merged_headers.update(self.settings.openapi_headers())

        return self.transport.request(
            method.upper(),
            f"{self.settings.base_url}{normalized_path}",
            headers=merged_headers,
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
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
        )

    def call_hyc_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
        )

    def call_ydz_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
        )

    def call_hkj_api(
        self,
        path: str,
        *,
        method: str = "POST",
        body: Any = None,
        query: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> Any:
        return self.call_chanjet_api(
            path=path,
            method=method,
            body=body,
            query=query,
            headers=headers,
        )

    def get_auth_url(
        self,
        redirect_uri: str,
        state: str | None = None,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> str:
        if not self.settings.app_key:
            raise ValueError("CHANJET_APP_KEY is required")
        if not redirect_uri:
            raise ValueError("redirect_uri is required")

        params = {
            "app_key": self.settings.app_key,
            "redirect_uri": redirect_uri,
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
        redirect_uri: str,
        *,
        timestamp: str | None = None,
        nonce: str | None = None,
    ) -> dict[str, Any]:
        if not code:
            raise ValueError("code is required")
        if not redirect_uri:
            raise ValueError("redirect_uri is required")
        params = self._token_params(
            grant_type="authorization_code",
            timestamp=timestamp,
            nonce=nonce,
        )
        params["code"] = code
        params["redirect_uri"] = redirect_uri
        params["sign"] = self._signature(params)
        response = self.transport.request(
            "GET", f"{self.settings.base_url}/auth/token", params=params
        )
        return self._normalize_token_response(response)

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
