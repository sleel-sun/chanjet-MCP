import os
import tempfile
import unittest
from pathlib import Path

from chanjet_tcloud_mcp.settings import ChanjetSettings


class SettingsTests(unittest.TestCase):
    def test_from_env_file_reads_credentials_and_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            env_path = Path(tmp_dir) / ".env"
            env_path.write_text(
                "\n".join(
                    [
                        "CHANJET_APP_KEY=app-key",
                        "CHANJET_APP_SECRET=app-secret",
                        "CHANJET_OPEN_TOKEN=open-token",
                        "CHANJET_REFRESH_TOKEN=refresh-token",
                        "CHANJET_ACTIVE_ACCOUNT=company-a",
                        "CHANJET_TOKEN_STORE_PATH=/tmp/chanjet-tokens.json",
                        "CHANJET_REDIRECT_URI=https://client-a.example.com/oauth/callback",
                    ]
                ),
                encoding="utf-8",
            )

            settings = ChanjetSettings.from_env_file(env_path)

        self.assertEqual(settings.app_key, "app-key")
        self.assertEqual(settings.app_secret, "app-secret")
        self.assertEqual(settings.open_token, "open-token")
        self.assertEqual(settings.refresh_token, "refresh-token")
        self.assertEqual(settings.active_account, "company-a")
        self.assertEqual(settings.token_store_path, "/tmp/chanjet-tokens.json")
        self.assertEqual(
            settings.redirect_uri, "https://client-a.example.com/oauth/callback"
        )
        self.assertEqual(settings.base_url, "https://openapi.chanjet.com")
        self.assertEqual(
            settings.docs_api_url, "https://openapi.chanjet.com/developer/api"
        )

    def test_from_env_prefers_process_environment_over_file(self):
        old_value = os.environ.get("CHANJET_APP_KEY")
        os.environ["CHANJET_APP_KEY"] = "process-key"
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                env_path = Path(tmp_dir) / ".env"
                env_path.write_text("CHANJET_APP_KEY=file-key\n", encoding="utf-8")

                settings = ChanjetSettings.from_env_file(env_path)
        finally:
            if old_value is None:
                os.environ.pop("CHANJET_APP_KEY", None)
            else:
                os.environ["CHANJET_APP_KEY"] = old_value

        self.assertEqual(settings.app_key, "process-key")

    def test_tplus_headers_require_credentials_and_token(self):
        settings = ChanjetSettings(
            app_key="app-key",
            app_secret="app-secret",
            open_token="open-token",
        )

        self.assertEqual(
            settings.tplus_headers(),
            {
                "appKey": "app-key",
                "appSecret": "app-secret",
                "openToken": "open-token",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        with self.assertRaises(ValueError):
            ChanjetSettings(app_key="app-key").tplus_headers()
