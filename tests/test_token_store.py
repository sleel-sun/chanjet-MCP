import os
import stat
import tempfile
import unittest
from pathlib import Path

from chanjet_tcloud_mcp.token_store import TokenStore


class TokenStoreTests(unittest.TestCase):
    def test_save_token_response_persists_account_and_returns_safe_summary(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "tokens.json"
            store = TokenStore(path)

            summary = store.save_token_response(
                "company-a",
                {
                    "access_token": "open-token-a",
                    "refresh_token": "refresh-token-a",
                    "expires_in": 100,
                    "raw": {
                        "accessToken": "open-token-a",
                        "refreshToken": "refresh-token-a",
                        "expiresIn": 100,
                        "orgId": "org-1",
                    },
                },
                now=1_000,
                make_active=True,
            )

            self.assertEqual(summary["account_alias"], "company-a")
            self.assertTrue(summary["active"])
            self.assertTrue(summary["has_open_token"])
            self.assertTrue(summary["has_refresh_token"])
            self.assertEqual(summary["expires_at"], 1_100)
            self.assertNotIn("open-token-a", str(summary))
            self.assertNotIn("refresh-token-a", str(summary))

            reloaded = TokenStore(path)
            account = reloaded.get_account("company-a")

            self.assertEqual(account["open_token"], "open-token-a")
            self.assertEqual(account["refresh_token"], "refresh-token-a")
            self.assertEqual(account["expires_at"], 1_100)
            self.assertEqual(reloaded.get_active_account_alias(), "company-a")
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o600)

    def test_set_active_account_and_delete_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = TokenStore(Path(tmp_dir) / "tokens.json")
            store.save_token_response(
                "company-a",
                {"access_token": "open-a", "refresh_token": "refresh-a"},
            )
            store.save_token_response(
                "company-b",
                {"access_token": "open-b", "refresh_token": "refresh-b"},
            )

            active_summary = store.set_active_account("company-b")
            deleted_summary = store.delete_account("company-b")

            self.assertEqual(active_summary["account_alias"], "company-b")
            self.assertTrue(active_summary["active"])
            self.assertEqual(deleted_summary["account_alias"], "company-b")
            self.assertIsNone(store.get_active_account_alias())
            self.assertIsNone(store.get_account("company-b"))
            self.assertIsNotNone(store.get_account("company-a"))

    def test_invalid_account_alias_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = TokenStore(Path(tmp_dir) / "tokens.json")

            with self.assertRaises(ValueError):
                store.save_token_response("../secret", {"access_token": "open"})


if __name__ == "__main__":
    unittest.main()
