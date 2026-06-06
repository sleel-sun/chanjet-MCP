from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path
from typing import Any


ALIAS_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")
DEFAULT_TOKEN_STORE_PATH = ".chanjet_tokens.json"
TOKEN_FIELD_NAMES = {
    "accesstoken",
    "opentoken",
    "refreshtoken",
}


class TokenStore:
    def __init__(self, path: str | Path = DEFAULT_TOKEN_STORE_PATH):
        self.path = Path(path)

    def save_token_response(
        self,
        account_alias: str,
        token_response: dict[str, Any],
        *,
        now: int | float | None = None,
        make_active: bool = False,
    ) -> dict[str, Any]:
        alias = self._validate_alias(account_alias)
        data = self._read_data()
        accounts = data["accounts"]
        existing = accounts.get(alias, {})

        open_token = (
            token_response.get("access_token")
            or token_response.get("open_token")
            or existing.get("open_token")
        )
        refresh_token = token_response.get("refresh_token") or existing.get(
            "refresh_token"
        )
        if not open_token and not refresh_token:
            raise ValueError("token_response must include access_token or refresh_token")

        timestamp = int(now if now is not None else time.time())
        expires_at = existing.get("expires_at")
        expires_in = token_response.get("expires_in")
        if expires_in is not None:
            try:
                expires_at = timestamp + int(expires_in)
            except (TypeError, ValueError) as exc:
                raise ValueError("expires_in must be an integer number of seconds") from exc

        metadata = self._safe_metadata(token_response.get("raw"))
        accounts[alias] = {
            "open_token": open_token,
            "refresh_token": refresh_token,
            "expires_at": expires_at,
            "metadata": metadata or existing.get("metadata") or {},
            "updated_at": timestamp,
        }
        if make_active:
            data["active_account"] = alias

        self._write_data(data)
        return self._summary(alias, accounts[alias], data.get("active_account"))

    def list_account_summaries(
        self, *, active_alias: str | None = None
    ) -> list[dict[str, Any]]:
        data = self._read_data()
        active = active_alias or data.get("active_account")
        return [
            self._summary(alias, account, active)
            for alias, account in sorted(data["accounts"].items())
        ]

    def get_account_summary(
        self, account_alias: str, *, active_alias: str | None = None
    ) -> dict[str, Any] | None:
        alias = self._validate_alias(account_alias)
        data = self._read_data()
        account = data["accounts"].get(alias)
        if account is None:
            return None
        return self._summary(alias, account, active_alias or data.get("active_account"))

    def get_account(self, account_alias: str) -> dict[str, Any] | None:
        alias = self._validate_alias(account_alias)
        account = self._read_data()["accounts"].get(alias)
        return dict(account) if account is not None else None

    def get_active_account_alias(self) -> str | None:
        active = self._read_data().get("active_account")
        return str(active) if active else None

    def set_active_account(self, account_alias: str) -> dict[str, Any]:
        alias = self._validate_alias(account_alias)
        data = self._read_data()
        account = data["accounts"].get(alias)
        if account is None:
            raise ValueError(f"Unknown Chanjet account alias: {alias}")
        data["active_account"] = alias
        self._write_data(data)
        return self._summary(alias, account, alias)

    def delete_account(self, account_alias: str) -> dict[str, Any]:
        alias = self._validate_alias(account_alias)
        data = self._read_data()
        account = data["accounts"].pop(alias, None)
        if account is None:
            raise ValueError(f"Unknown Chanjet account alias: {alias}")
        if data.get("active_account") == alias:
            data["active_account"] = None
        self._write_data(data)
        return self._summary(alias, account, None)

    def _read_data(self) -> dict[str, Any]:
        if not self.path.exists():
            return {"active_account": None, "accounts": {}}

        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid Chanjet token store JSON: {self.path}") from exc

        if not isinstance(raw, dict):
            raise ValueError(f"Invalid Chanjet token store format: {self.path}")
        accounts = raw.get("accounts", {})
        if not isinstance(accounts, dict):
            raise ValueError(f"Invalid Chanjet token store accounts: {self.path}")
        active_account = raw.get("active_account")
        if active_account is not None:
            active_account = self._validate_alias(str(active_account))
        return {"active_account": active_account, "accounts": accounts}

    def _write_data(self, data: dict[str, Any]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp_path = self.path.with_name(f".{self.path.name}.tmp")
        payload = json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True)

        fd = os.open(str(temp_path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.write("\n")
        except Exception:
            try:
                temp_path.unlink()
            except FileNotFoundError:
                pass
            raise

        os.replace(temp_path, self.path)
        try:
            os.chmod(self.path, 0o600)
        except OSError:
            pass

    def _summary(
        self,
        account_alias: str,
        account: dict[str, Any],
        active_alias: str | None,
    ) -> dict[str, Any]:
        return {
            "account_alias": account_alias,
            "active": account_alias == active_alias,
            "has_open_token": bool(account.get("open_token")),
            "has_refresh_token": bool(account.get("refresh_token")),
            "expires_at": account.get("expires_at"),
            "metadata": account.get("metadata") or {},
            "updated_at": account.get("updated_at"),
        }

    def _safe_metadata(self, raw: Any) -> dict[str, Any]:
        if not isinstance(raw, dict):
            return {}
        return {
            key: value
            for key, value in raw.items()
            if key.replace("_", "").casefold() not in TOKEN_FIELD_NAMES
        }

    def _validate_alias(self, account_alias: str) -> str:
        alias = account_alias.strip()
        if not ALIAS_PATTERN.fullmatch(alias):
            raise ValueError(
                "account_alias must be 1-128 characters using letters, numbers, dot, underscore, or hyphen"
            )
        return alias
