import unittest

from chanjet_tcloud_mcp.client import ChanjetApiError, ChanjetTCloudClient
from chanjet_tcloud_mcp.settings import ChanjetSettings


class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def request(self, method, url, *, headers=None, params=None, json_body=None):
        self.calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers or {},
                "params": params or {},
                "json_body": json_body,
            }
        )
        if not self.responses:
            raise AssertionError("No fake response configured")
        return self.responses.pop(0)


class ClientTests(unittest.TestCase):
    def make_client(self, responses, settings=None):
        settings = settings or ChanjetSettings(
            app_key="app-key",
            app_secret="app-secret",
            open_token="open-token",
        )
        transport = FakeTransport(responses)
        return ChanjetTCloudClient(settings=settings, transport=transport), transport

    def test_list_tcloud_modules_unwraps_official_document_envelope(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "tcloud",
                        "children": [
                            {
                                "moduleCode": "t+jcda",
                                "moduleName": "T+基础档案",
                                "children": [
                                    {
                                        "moduleCode": "t+ck",
                                        "moduleName": "仓库",
                                    }
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.list_tcloud_modules()

        self.assertEqual(result["productCode"], "tcloud")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/tcloud",
        )

    def test_get_tcloud_doc_encodes_module_codes(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"modulePath": "T+ API", "documentApiInfoList": []},
                }
            ]
        )

        result = client.get_tcloud_doc("t+jcda", "t+ck")

        self.assertEqual(result["modulePath"], "T+ API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bjcda/t%2Bck",
        )

    def test_search_tcloud_docs_matches_module_code_and_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "tcloud",
                        "children": [
                            {
                                "moduleCode": "t+jcda",
                                "moduleName": "T+基础档案",
                                "children": [
                                    {
                                        "moduleCode": "t+ck",
                                        "moduleName": "仓库",
                                    },
                                    {
                                        "moduleCode": "t+ch",
                                        "moduleName": "存货",
                                    },
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.search_tcloud_docs("仓库")

        self.assertEqual(
            result,
            [
                {
                    "parent_code": "t+jcda",
                    "parent_name": "T+基础档案",
                    "module_code": "t+ck",
                    "module_name": "仓库",
                    "path": ["tcloud", "t+jcda", "t+ck"],
                }
            ],
        )

    def test_document_api_error_includes_code_message_and_trace(self):
        client, _transport = self.make_client(
            [
                {
                    "result": False,
                    "error": {
                        "code": "500",
                        "msg": "Internal Server Error",
                        "hint": "bad path",
                    },
                    "value": None,
                    "traceId": "trace-1",
                }
            ]
        )

        with self.assertRaises(ChanjetApiError) as raised:
            client.list_tcloud_modules()

        self.assertEqual(raised.exception.code, "500")
        self.assertEqual(raised.exception.message, "Internal Server Error")
        self.assertEqual(raised.exception.hint, "bad path")
        self.assertEqual(raised.exception.trace_id, "trace-1")

    def test_call_tplus_api_injects_auth_headers_and_body(self):
        client, transport = self.make_client([{"code": "0", "data": [{"Code": "01"}]}])

        result = client.call_tplus_api(
            "/tplus/api/v2/warehouse/Query",
            body={"param": {"Code": "01"}},
        )

        self.assertEqual(result, {"code": "0", "data": [{"Code": "01"}]})
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/tplus/api/v2/warehouse/Query",
        )
        self.assertEqual(transport.calls[0]["method"], "POST")
        self.assertEqual(transport.calls[0]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[0]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[0]["headers"]["openToken"], "open-token")
        self.assertEqual(transport.calls[0]["json_body"], {"param": {"Code": "01"}})

    def test_get_auth_url_contains_oauth_parameters_and_signature(self):
        settings = ChanjetSettings(app_key="app-key")
        client, _transport = self.make_client([], settings=settings)

        url = client.get_auth_url(
            redirect_uri="https://example.test/oauth/callback",
            state="state-1",
            timestamp="1700000000",
            nonce="nonce-1",
        )

        self.assertIn("https://openapi.chanjet.com/oauth/authorize?", url)
        self.assertIn("app_key=app-key", url)
        self.assertIn("redirect_uri=https%3A%2F%2Fexample.test%2Foauth%2Fcallback", url)
        self.assertIn("response_type=code", url)
        self.assertIn("state=state-1", url)
        self.assertIn("timestamp=1700000000", url)
        self.assertIn("nonce=nonce-1", url)
        self.assertIn("sign=", url)

    def test_exchange_token_normalizes_access_token_response(self):
        client, transport = self.make_client(
            [
                {
                    "code": "200",
                    "result": {
                        "accessToken": "new-open-token",
                        "refreshToken": "new-refresh-token",
                        "expiresIn": 518400,
                    },
                }
            ]
        )

        result = client.exchange_token(
            code="auth-code",
            redirect_uri="https://example.test/oauth/callback",
            timestamp="1700000300",
            nonce="nonce-2",
        )

        self.assertEqual(
            result,
            {
                "access_token": "new-open-token",
                "refresh_token": "new-refresh-token",
                "expires_in": 518400,
                "raw": {
                    "accessToken": "new-open-token",
                    "refreshToken": "new-refresh-token",
                    "expiresIn": 518400,
                },
            },
        )
        self.assertEqual(
            transport.calls[0]["url"], "https://openapi.chanjet.com/auth/token"
        )
        self.assertEqual(transport.calls[0]["params"]["grant_type"], "authorization_code")
        self.assertEqual(transport.calls[0]["params"]["code"], "auth-code")
        self.assertIn("sign", transport.calls[0]["params"])

