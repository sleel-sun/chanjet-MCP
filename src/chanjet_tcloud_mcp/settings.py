from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping


DEFAULT_BASE_URL = "https://openapi.chanjet.com"
DEFAULT_DOCS_API_URL = "https://openapi.chanjet.com/developer/api"


@dataclass(frozen=True)
class ChanjetSettings:
    app_key: str | None = None
    app_secret: str | None = None
    open_token: str | None = None
    refresh_token: str | None = None
    base_url: str = DEFAULT_BASE_URL
    docs_api_url: str = DEFAULT_DOCS_API_URL
    timeout_seconds: float = 30.0

    @classmethod
    def from_env_file(
        cls,
        env_path: str | Path = ".env",
        environ: Mapping[str, str] | None = None,
    ) -> "ChanjetSettings":
        file_values = _read_env_file(Path(env_path))
        env_values = environ if environ is not None else os.environ

        def get(name: str, default: str | None = None) -> str | None:
            return env_values.get(name) or file_values.get(name) or default

        timeout_value = get("CHANJET_TIMEOUT_SECONDS", "30")
        try:
            timeout_seconds = float(timeout_value or "30")
        except ValueError as exc:
            raise ValueError("CHANJET_TIMEOUT_SECONDS must be a number") from exc

        return cls(
            app_key=get("CHANJET_APP_KEY"),
            app_secret=get("CHANJET_APP_SECRET"),
            open_token=get("CHANJET_OPEN_TOKEN"),
            refresh_token=get("CHANJET_REFRESH_TOKEN"),
            base_url=(get("CHANJET_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL).rstrip(
                "/"
            ),
            docs_api_url=(
                get("CHANJET_DOCS_API_URL", DEFAULT_DOCS_API_URL)
                or DEFAULT_DOCS_API_URL
            ).rstrip("/"),
            timeout_seconds=timeout_seconds,
        )

    def openapi_headers(self) -> dict[str, str]:
        missing = [
            name
            for name, value in (
                ("CHANJET_APP_KEY", self.app_key),
                ("CHANJET_APP_SECRET", self.app_secret),
                ("CHANJET_OPEN_TOKEN", self.open_token),
            )
            if not value
        ]
        if missing:
            raise ValueError("Missing required Chanjet settings: " + ", ".join(missing))

        return {
            "appKey": self.app_key or "",
            "appSecret": self.app_secret or "",
            "openToken": self.open_token or "",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def tplus_headers(self) -> dict[str, str]:
        return self.openapi_headers()


def _read_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values
