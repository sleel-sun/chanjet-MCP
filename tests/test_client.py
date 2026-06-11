import unittest
import tempfile
from pathlib import Path

from chanjet_tcloud_mcp.client import ChanjetApiError, ChanjetTCloudClient
from chanjet_tcloud_mcp.settings import ChanjetSettings
from chanjet_tcloud_mcp.token_store import TokenStore


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
    def make_client(self, responses, settings=None, token_store=None):
        settings = settings or ChanjetSettings(
            app_key="app-key",
            app_secret="app-secret",
            open_token="open-token",
        )
        transport = FakeTransport(responses)
        return (
            ChanjetTCloudClient(
                settings=settings,
                transport=transport,
                token_store=token_store,
            ),
            transport,
        )

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

    def test_list_hyc_modules_uses_zplus_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "zplus",
                        "productName": "好业财API",
                        "children": [],
                    },
                }
            ]
        )

        result = client.list_hyc_modules()

        self.assertEqual(result["productCode"], "zplus")
        self.assertEqual(result["productName"], "好业财API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/zplus",
        )

    def test_get_hyc_doc_encodes_zplus_module_codes(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"modulePath": "好业财API", "documentApiInfoList": []},
                }
            ]
        )

        result = client.get_hyc_doc("zjjcda", " hyc_msg")

        self.assertEqual(result["modulePath"], "好业财API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/zplus/zjjcda/%20hyc_msg",
        )

    def test_search_hyc_docs_matches_module_code_and_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "zplus",
                        "children": [
                            {
                                "moduleCode": "zjjcda",
                                "moduleName": "好业财基础档案",
                                "children": [
                                    {
                                        "moduleCode": "ck",
                                        "moduleName": "仓库",
                                    },
                                    {
                                        "moduleCode": "sp",
                                        "moduleName": "商品",
                                    },
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.search_hyc_docs("仓库")

        self.assertEqual(
            result,
            [
                {
                    "parent_code": "zjjcda",
                    "parent_name": "好业财基础档案",
                    "module_code": "ck",
                    "module_name": "仓库",
                    "path": ["zplus", "zjjcda", "ck"],
                }
            ],
        )

    def test_call_hyc_api_injects_auth_headers_and_body(self):
        client, transport = self.make_client(
            [{"code": "openApi.e0000", "data": {"count": 1}}]
        )

        result = client.call_hyc_api(
            "/accounting/openapi/cc/warehouse/list/123",
            body={"pageSize": 20, "pageNo": 1},
        )

        self.assertEqual(result, {"code": "openApi.e0000", "data": {"count": 1}})
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/accounting/openapi/cc/warehouse/list/123",
        )
        self.assertEqual(transport.calls[0]["method"], "POST")
        self.assertEqual(transport.calls[0]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[0]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[0]["headers"]["openToken"], "open-token")
        self.assertEqual(transport.calls[0]["json_body"], {"pageSize": 20, "pageNo": 1})

    def test_list_hsy_modules_uses_hsy_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "hsy",
                        "productName": "好生意",
                        "children": [],
                    },
                }
            ]
        )

        result = client.list_hsy_modules()

        self.assertEqual(result["productCode"], "hsy")
        self.assertEqual(result["productName"], "好生意")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/hsy",
        )

    def test_get_hsy_doc_uses_hsy_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"modulePath": "好生意API", "documentApiInfoList": []},
                }
            ]
        )

        result = client.get_hsy_doc("hsyxxdy", "hsy_product")

        self.assertEqual(result["modulePath"], "好生意API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/hsy/hsyxxdy/hsy_product",
        )

    def test_search_hsy_docs_matches_module_code_and_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "hsy",
                        "children": [
                            {
                                "moduleCode": "hsyxxdy",
                                "moduleName": "好生意消息订阅",
                                "children": [
                                    {
                                        "moduleCode": "hsy_product",
                                        "moduleName": "商品",
                                    },
                                    {
                                        "moduleCode": "hsy_warehouse_message",
                                        "moduleName": "仓库",
                                    },
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.search_hsy_docs("仓库")

        self.assertEqual(
            result,
            [
                {
                    "parent_code": "hsyxxdy",
                    "parent_name": "好生意消息订阅",
                    "module_code": "hsy_warehouse_message",
                    "module_name": "仓库",
                    "path": ["hsy", "hsyxxdy", "hsy_warehouse_message"],
                }
            ],
        )

    def test_call_hsy_api_injects_auth_headers_and_body(self):
        client, transport = self.make_client(
            [{"code": "openApi.e0000", "data": {"count": 1}}]
        )

        result = client.call_hsy_api(
            "/accounting/openapi/cc/warehouse/list/123",
            body={"pageSize": 20, "pageNo": 1},
        )

        self.assertEqual(result, {"code": "openApi.e0000", "data": {"count": 1}})
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/accounting/openapi/cc/warehouse/list/123",
        )
        self.assertEqual(transport.calls[0]["method"], "POST")
        self.assertEqual(transport.calls[0]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[0]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[0]["headers"]["openToken"], "open-token")
        self.assertEqual(transport.calls[0]["json_body"], {"pageSize": 20, "pageNo": 1})

    def test_list_ydz_modules_uses_finance_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "finance",
                        "productName": "易代账",
                        "children": [],
                    },
                }
            ]
        )

        result = client.list_ydz_modules()

        self.assertEqual(result["productCode"], "finance")
        self.assertEqual(result["productName"], "易代账")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/finance",
        )

    def test_get_ydz_doc_uses_finance_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"modulePath": "易代账API", "documentApiInfoList": []},
                }
            ]
        )

        result = client.get_ydz_doc("ydzjcda", "ck")

        self.assertEqual(result["modulePath"], "易代账API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/finance/ydzjcda/ck",
        )

    def test_search_ydz_docs_matches_module_code_and_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "finance",
                        "children": [
                            {
                                "moduleCode": "ydzjcda",
                                "moduleName": "易代账-基础档案",
                                "children": [
                                    {
                                        "moduleCode": "ck",
                                        "moduleName": "仓库",
                                    },
                                    {
                                        "moduleCode": "sp",
                                        "moduleName": "商品",
                                    },
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.search_ydz_docs("仓库")

        self.assertEqual(
            result,
            [
                {
                    "parent_code": "ydzjcda",
                    "parent_name": "易代账-基础档案",
                    "module_code": "ck",
                    "module_name": "仓库",
                    "path": ["finance", "ydzjcda", "ck"],
                }
            ],
        )

    def test_call_ydz_api_injects_auth_headers_and_body(self):
        client, transport = self.make_client(
            [{"successResultMap": {"WH001": "123"}, "failResultMap": {}}]
        )

        result = client.call_ydz_api(
            "/accounting/document/integration/warehouse/batchUpsertt/123",
            body=[
                {
                    "id": "WH001",
                    "code": "WH001",
                    "name": "仓库",
                    "statusEnum": "A",
                }
            ],
        )

        self.assertEqual(result, {"successResultMap": {"WH001": "123"}, "failResultMap": {}})
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/accounting/document/integration/warehouse/batchUpsertt/123",
        )
        self.assertEqual(transport.calls[0]["method"], "POST")
        self.assertEqual(transport.calls[0]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[0]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[0]["headers"]["openToken"], "open-token")
        self.assertEqual(
            transport.calls[0]["json_body"],
            [
                {
                    "id": "WH001",
                    "code": "WH001",
                    "name": "仓库",
                    "statusEnum": "A",
                }
            ],
        )

    def test_list_hkj_modules_uses_accounting_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "accounting",
                        "productName": "好会计API",
                        "children": [],
                    },
                }
            ]
        )

        result = client.list_hkj_modules()

        self.assertEqual(result["productCode"], "accounting")
        self.assertEqual(result["productName"], "好会计API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/accounting",
        )

    def test_get_hkj_doc_uses_accounting_product_code(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {"modulePath": "好会计API", "documentApiInfoList": []},
                }
            ]
        )

        result = client.get_hkj_doc("jcda", "ck")

        self.assertEqual(result["modulePath"], "好会计API")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/accounting/jcda/ck",
        )

    def test_search_hkj_docs_matches_module_code_and_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "productCode": "accounting",
                        "children": [
                            {
                                "moduleCode": "jcda",
                                "moduleName": "基础档案",
                                "children": [
                                    {
                                        "moduleCode": "ck",
                                        "moduleName": "仓库",
                                    },
                                    {
                                        "moduleCode": "sp",
                                        "moduleName": "商品",
                                    },
                                ],
                            }
                        ],
                    },
                }
            ]
        )

        result = client.search_hkj_docs("仓库")

        self.assertEqual(
            result,
            [
                {
                    "parent_code": "jcda",
                    "parent_name": "基础档案",
                    "module_code": "ck",
                    "module_name": "仓库",
                    "path": ["accounting", "jcda", "ck"],
                }
            ],
        )

    def test_call_hkj_api_injects_auth_headers_and_body(self):
        client, transport = self.make_client(
            [{"successResultMap": {"HKJ001": "123"}, "failResultMap": {}}]
        )

        result = client.call_hkj_api(
            "/accounting/document/integration/warehouse/batchUpsertt/123",
            body=[
                {
                    "id": "HKJ001",
                    "code": "HKJ001",
                    "name": "仓库",
                    "statusEnum": "A",
                }
            ],
        )

        self.assertEqual(
            result,
            {"successResultMap": {"HKJ001": "123"}, "failResultMap": {}},
        )
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/accounting/document/integration/warehouse/batchUpsertt/123",
        )
        self.assertEqual(transport.calls[0]["method"], "POST")
        self.assertEqual(transport.calls[0]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[0]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[0]["headers"]["openToken"], "open-token")
        self.assertEqual(
            transport.calls[0]["json_body"],
            [
                {
                    "id": "HKJ001",
                    "code": "HKJ001",
                    "name": "仓库",
                    "statusEnum": "A",
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

    def test_query_tplus_voucher_list_fetches_and_matches_display_fields(self):
        client, transport = self.make_client(
            [
                {
                    "code": "0",
                    "data": {
                        "columns": [
                            {"FieldName": "Code", "Caption": "单据编号"},
                            {"FieldName": "CustomerName", "Caption": "客户"},
                            {"FieldName": "Amount", "Caption": "金额"},
                        ]
                    },
                },
                {"code": "0", "data": [{"Code": "SA-001", "CustomerName": "客户A"}]},
            ]
        )

        result = client.query_tplus_voucher_list(
            biz_code="SA03",
            path="/tplus/api/v2/saleDelivery/Query",
            body={"param": {"pageIndex": 1}},
            display_fields=["单据编号", "客户", "不存在字段"],
        )

        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/tplus/api/v2/VoucherAPIService/GetColumnSetByBizCode",
        )
        self.assertEqual(
            transport.calls[0]["json_body"],
            {"bizCode": "SA03", "apiParam": {"dataSource": "openapi"}},
        )
        self.assertEqual(
            transport.calls[1]["url"],
            "https://openapi.chanjet.com/tplus/api/v2/saleDelivery/Query",
        )
        self.assertEqual(
            transport.calls[1]["json_body"],
            {"param": {"pageIndex": 1, "selectFields": ["Code", "CustomerName"]}},
        )
        self.assertEqual(
            result["data"],
            {"code": "0", "data": [{"Code": "SA-001", "CustomerName": "客户A"}]},
        )
        self.assertEqual(
            result["matched_display_fields"],
            [
                {"requested": "单据编号", "field": "Code", "label": "单据编号"},
                {"requested": "客户", "field": "CustomerName", "label": "客户"},
            ],
        )
        self.assertEqual(result["unmatched_display_fields"], ["不存在字段"])
        self.assertEqual(
            [field["field"] for field in result["display_fields"]],
            ["Code", "CustomerName", "Amount"],
        )

    def test_query_tplus_voucher_list_preserves_existing_field_selection(self):
        client, transport = self.make_client(
            [
                {
                    "code": "0",
                    "data": [
                        {"field": "Code", "title": "单据编号"},
                        {"field": "CustomerName", "title": "客户"},
                    ],
                },
                {"code": "0", "data": []},
            ]
        )

        client.query_tplus_voucher_list(
            biz_code="SA03",
            path="/tplus/api/v2/saleDelivery/Query",
            body={"param": {"selectFields": ["ExistingField"]}},
            display_fields=["单据编号"],
        )

        self.assertEqual(
            transport.calls[1]["json_body"],
            {"param": {"selectFields": ["ExistingField"]}},
        )

    def test_diagnose_config_reports_missing_credentials(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            settings = ChanjetSettings(token_store_path=str(Path(tmp_dir) / "tokens.json"))
            client, _transport = self.make_client(
                [],
                settings=settings,
                token_store=token_store,
            )

            result = client.diagnose_config(now=1_000)

            self.assertFalse(result["settings"]["has_app_key"])
            self.assertFalse(result["settings"]["has_app_secret"])
            self.assertFalse(result["settings"]["has_redirect_uri"])
            self.assertEqual(result["accounts"]["stored_account_count"], 0)
            self.assertIsNone(result["accounts"]["active_account"])
            self.assertFalse(result["accounts"]["has_active_open_token"])
            self.assertFalse(result["accounts"]["has_active_refresh_token"])
            self.assertTrue(result["capabilities"]["documentation_lookup"])
            self.assertFalse(result["capabilities"]["oauth_url_generation"])
            self.assertFalse(result["capabilities"]["token_exchange"])
            self.assertFalse(result["capabilities"]["business_api_calls"])
            self.assertEqual(
                {issue["code"] for issue in result["issues"]},
                {
                    "missing_app_key",
                    "missing_app_secret",
                    "missing_redirect_uri",
                    "missing_token",
                },
            )

    def test_diagnose_config_reports_active_stored_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {
                    "access_token": "stored-open-token",
                    "refresh_token": "stored-refresh-token",
                    "expires_in": 600,
                },
                now=1_000,
                make_active=True,
            )
            settings = ChanjetSettings(
                app_key="app-key",
                app_secret="app-secret",
                redirect_uri="https://example.test/oauth/callback",
                token_store_path=str(Path(tmp_dir) / "tokens.json"),
            )
            client, _transport = self.make_client(
                [],
                settings=settings,
                token_store=token_store,
            )

            result = client.diagnose_config(now=1_100)

            self.assertTrue(result["settings"]["has_app_key"])
            self.assertTrue(result["settings"]["has_app_secret"])
            self.assertTrue(result["settings"]["has_redirect_uri"])
            self.assertEqual(result["accounts"]["stored_account_count"], 1)
            self.assertEqual(result["accounts"]["active_account"], "company-a")
            self.assertTrue(result["accounts"]["active_account_exists"])
            self.assertTrue(result["accounts"]["has_active_open_token"])
            self.assertTrue(result["accounts"]["has_active_refresh_token"])
            self.assertFalse(result["accounts"]["active_token_expired"])
            self.assertTrue(result["capabilities"]["oauth_url_generation"])
            self.assertTrue(result["capabilities"]["token_exchange"])
            self.assertTrue(result["capabilities"]["business_api_calls"])
            self.assertEqual(result["issues"], [])
            self.assertNotIn("stored-open-token", str(result))
            self.assertNotIn("stored-refresh-token", str(result))

    def test_diagnose_config_does_not_use_legacy_token_with_unknown_active_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            settings = ChanjetSettings(
                app_key="app-key",
                app_secret="app-secret",
                open_token="legacy-open-token",
                active_account="missing-company",
                token_store_path=str(Path(tmp_dir) / "tokens.json"),
            )
            client, _transport = self.make_client(
                [],
                settings=settings,
                token_store=token_store,
            )

            result = client.diagnose_config(now=1_000)

            self.assertFalse(result["capabilities"]["business_api_calls"])
            self.assertEqual(
                {issue["code"] for issue in result["issues"]},
                {"missing_redirect_uri", "unknown_active_account", "missing_token"},
            )
            self.assertNotIn("legacy-open-token", str(result))

    def test_get_api_call_template_extracts_tplus_templates(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "T+Cloud / 基础档案 / 仓库",
                        "moduleName": "仓库",
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库查询",
                                "apiUrl": "/tplus/api/v2/warehouse/Query",
                                "requestMethod": "POST",
                                "requestBody": {"param": {"Code": "01"}},
                            }
                        ],
                    },
                }
            ]
        )

        result = client.get_api_call_template(
            product="tplus",
            parent_code="t+jcda",
            module_code="t+ck",
        )

        self.assertEqual(result["product"]["code"], "tcloud")
        self.assertEqual(result["product"]["tool"], "call_tplus_api")
        self.assertEqual(result["module"]["module_path"], "T+Cloud / 基础档案 / 仓库")
        self.assertEqual(len(result["templates"]), 1)
        template = result["templates"][0]
        self.assertEqual(template["api_name"], "仓库查询")
        self.assertEqual(template["path"], "/tplus/api/v2/warehouse/Query")
        self.assertEqual(template["method"], "POST")
        self.assertEqual(template["body"], {"param": {"Code": "01"}})
        self.assertEqual(template["tool"], "call_tplus_api")
        self.assertEqual(
            template["arguments"],
            {
                "path": "/tplus/api/v2/warehouse/Query",
                "method": "POST",
                "body": {"param": {"Code": "01"}},
                "query": {},
                "headers": {},
                "account_alias": None,
            },
        )
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bjcda/t%2Bck",
        )

    def test_get_api_call_template_extracts_hsy_templates(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "好生意 / 消息订阅 / 仓库",
                        "moduleName": "仓库",
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库查询",
                                "apiUrl": "/accounting/openapi/cc/warehouse/list/123",
                                "requestMethod": "POST",
                            }
                        ],
                    },
                }
            ]
        )

        result = client.get_api_call_template(
            product="hsy",
            parent_code="hsyxxdy",
            module_code="hsy_warehouse_message",
        )

        self.assertEqual(result["product"]["code"], "hsy")
        self.assertEqual(result["product"]["tool"], "call_hsy_api")
        self.assertEqual(result["templates"][0]["tool"], "call_hsy_api")
        self.assertEqual(
            transport.calls[0]["url"],
            "https://openapi.chanjet.com/developer/api/doc-center/details/hsy/hsyxxdy/hsy_warehouse_message",
        )

    def test_get_api_call_template_filters_by_api_name(self):
        client, _transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库查询",
                                "apiUrl": "/tplus/api/v2/warehouse/Query",
                            },
                            {
                                "apiName": "仓库新增",
                                "apiUrl": "/tplus/api/v2/warehouse/Create",
                            },
                        ],
                    },
                }
            ]
        )

        result = client.get_api_call_template(
            product="tcloud",
            parent_code="t+jcda",
            module_code="t+ck",
            api_name="新增",
        )

        self.assertEqual(len(result["templates"]), 1)
        self.assertEqual(result["templates"][0]["api_name"], "仓库新增")
        self.assertEqual(result["templates"][0]["path"], "/tplus/api/v2/warehouse/Create")

    def test_search_api_templates_returns_ready_to_call_templates(self):
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
                },
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "T+Cloud / 基础档案 / 仓库",
                        "moduleName": "仓库",
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库查询",
                                "apiUrl": "/tplus/api/v2/warehouse/Query",
                                "requestMethod": "POST",
                            }
                        ],
                    },
                },
            ]
        )

        result = client.search_api_templates(
            query="仓库",
            product="tplus",
            api_name="查询",
        )

        self.assertEqual(result["query"], "仓库")
        self.assertEqual(result["product"], "tplus")
        self.assertEqual(len(result["templates"]), 1)
        template = result["templates"][0]
        self.assertEqual(template["product"]["code"], "tcloud")
        self.assertEqual(template["module"]["parent_code"], "t+jcda")
        self.assertEqual(template["module"]["module_code"], "t+ck")
        self.assertEqual(template["api_name"], "仓库查询")
        self.assertEqual(template["tool"], "call_tplus_api")
        self.assertEqual(template["arguments"]["path"], "/tplus/api/v2/warehouse/Query")
        self.assertEqual(
            [call["url"] for call in transport.calls],
            [
                "https://openapi.chanjet.com/developer/api/doc-center/modulesNameByCode/tcloud",
                "https://openapi.chanjet.com/developer/api/doc-center/details/tcloud/t%2Bjcda/t%2Bck",
            ],
        )

    def test_call_api_template_routes_to_matching_product_call(self):
        client, transport = self.make_client(
            [
                {
                    "result": True,
                    "error": None,
                    "value": {
                        "modulePath": "T+Cloud / 基础档案 / 仓库",
                        "moduleName": "仓库",
                        "documentApiInfoList": [
                            {
                                "apiName": "仓库查询",
                                "apiUrl": "/tplus/api/v2/warehouse/Query",
                                "requestMethod": "POST",
                                "requestBody": {"param": {"Code": "from-template"}},
                            }
                        ],
                    },
                },
                {"code": "0", "data": [{"Code": "01"}]},
            ]
        )

        result = client.call_api_template(
            product="tplus",
            parent_code="t+jcda",
            module_code="t+ck",
            api_name="查询",
            body={"param": {"Code": "01"}},
        )

        self.assertEqual(result["template"]["api_name"], "仓库查询")
        self.assertEqual(result["request"]["path"], "/tplus/api/v2/warehouse/Query")
        self.assertEqual(result["request"]["body"], {"param": {"Code": "01"}})
        self.assertEqual(result["data"], {"code": "0", "data": [{"Code": "01"}]})
        self.assertEqual(
            transport.calls[1]["url"],
            "https://openapi.chanjet.com/tplus/api/v2/warehouse/Query",
        )
        self.assertEqual(transport.calls[1]["method"], "POST")
        self.assertEqual(transport.calls[1]["headers"]["appKey"], "app-key")
        self.assertEqual(transport.calls[1]["headers"]["appSecret"], "app-secret")
        self.assertEqual(transport.calls[1]["headers"]["openToken"], "open-token")
        self.assertEqual(
            transport.calls[1]["json_body"],
            {"param": {"Code": "01"}},
        )

    def test_tool_error_envelope_from_value_error(self):
        client, _transport = self.make_client([])

        result = client.tool_error(
            ValueError("product is required"),
            hint="Pass product such as tplus, hyc, ydz, or hkj.",
        )

        self.assertEqual(
            result,
            {
                "ok": False,
                "error": {
                    "code": "invalid_argument",
                    "message": "product is required",
                    "hint": "Pass product such as tplus, hyc, ydz, or hkj.",
                    "trace_id": None,
                },
            },
        )

    def test_safe_get_api_call_template_wraps_invalid_product(self):
        client, _transport = self.make_client([])

        result = client.safe_get_api_call_template(
            product="unknown",
            parent_code="p",
            module_code="m",
        )

        self.assertFalse(result["ok"])
        self.assertEqual(result["error"]["code"], "invalid_argument")
        self.assertIn("Unsupported product", result["error"]["message"])
        self.assertIn("tplus", result["error"]["hint"])

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

    def test_get_auth_url_uses_configured_redirect_uri_when_omitted(self):
        settings = ChanjetSettings(
            app_key="app-key",
            redirect_uri="https://client-a.example.com/oauth/callback",
        )
        client, _transport = self.make_client([], settings=settings)

        url = client.get_auth_url(
            state="state-1",
            timestamp="1700000000",
            nonce="nonce-1",
        )

        self.assertIn(
            "redirect_uri=https%3A%2F%2Fclient-a.example.com%2Foauth%2Fcallback",
            url,
        )

    def test_get_auth_url_prefers_explicit_redirect_uri(self):
        settings = ChanjetSettings(
            app_key="app-key",
            redirect_uri="https://client-a.example.com/oauth/callback",
        )
        client, _transport = self.make_client([], settings=settings)

        url = client.get_auth_url(
            redirect_uri="https://override.example.com/oauth/callback",
            state="state-1",
            timestamp="1700000000",
            nonce="nonce-1",
        )

        self.assertIn(
            "redirect_uri=https%3A%2F%2Foverride.example.com%2Foauth%2Fcallback",
            url,
        )

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

    def test_exchange_token_uses_configured_redirect_uri_when_omitted(self):
        settings = ChanjetSettings(
            app_key="app-key",
            app_secret="app-secret",
            redirect_uri="https://client-a.example.com/oauth/callback",
        )
        client, transport = self.make_client(
            [
                {
                    "code": "200",
                    "result": {
                        "accessToken": "new-open-token",
                        "refreshToken": "new-refresh-token",
                    },
                }
            ],
            settings=settings,
        )

        client.exchange_token(
            code="auth-code",
            timestamp="1700000300",
            nonce="nonce-2",
        )

        self.assertEqual(
            transport.calls[0]["params"]["redirect_uri"],
            "https://client-a.example.com/oauth/callback",
        )

    def test_oauth_complete_setup_stores_account_without_returning_token_values(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            settings = ChanjetSettings(app_key="app-key", app_secret="app-secret")
            client, transport = self.make_client(
                [
                    {
                        "code": "200",
                        "result": {
                            "accessToken": "stored-open-token",
                            "refreshToken": "stored-refresh-token",
                            "expiresIn": 600,
                            "orgId": "org-1",
                        },
                    }
                ],
                settings=settings,
                token_store=token_store,
            )

            summary = client.oauth_complete_setup(
                code="auth-code",
                redirect_uri="https://example.test/oauth/callback",
                account_alias="company-a",
                timestamp="1700000300",
                nonce="nonce-3",
                now=1_000,
            )

            self.assertEqual(summary["account_alias"], "company-a")
            self.assertTrue(summary["active"])
            self.assertTrue(summary["has_open_token"])
            self.assertTrue(summary["has_refresh_token"])
            self.assertEqual(summary["expires_at"], 1_600)
            self.assertNotIn("stored-open-token", str(summary))
            self.assertNotIn("stored-refresh-token", str(summary))
            self.assertEqual(
                token_store.get_account("company-a")["open_token"],
                "stored-open-token",
            )

    def test_oauth_complete_setup_uses_configured_redirect_uri_when_omitted(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            settings = ChanjetSettings(
                app_key="app-key",
                app_secret="app-secret",
                redirect_uri="https://client-a.example.com/oauth/callback",
            )
            client, transport = self.make_client(
                [
                    {
                        "code": "200",
                        "result": {
                            "accessToken": "stored-open-token",
                            "refreshToken": "stored-refresh-token",
                        },
                    }
                ],
                settings=settings,
                token_store=token_store,
            )

            summary = client.oauth_complete_setup(
                code="auth-code",
                account_alias="company-a",
                timestamp="1700000300",
                nonce="nonce-3",
                now=1_000,
            )

            self.assertEqual(summary["account_alias"], "company-a")
            self.assertEqual(
                transport.calls[0]["params"]["redirect_uri"],
                "https://client-a.example.com/oauth/callback",
            )
            self.assertEqual(transport.calls[0]["params"]["grant_type"], "authorization_code")

    def test_call_api_uses_selected_stored_account_token(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {
                    "access_token": "stored-open-token",
                    "refresh_token": "stored-refresh-token",
                },
                make_active=True,
            )
            settings = ChanjetSettings(app_key="app-key", app_secret="app-secret")
            client, transport = self.make_client(
                [{"code": "0", "data": []}],
                settings=settings,
                token_store=token_store,
            )

            result = client.call_tplus_api(
                "/tplus/api/v2/warehouse/Query",
                body={"param": {"Code": "01"}},
                account_alias="company-a",
            )

            self.assertEqual(result, {"code": "0", "data": []})
            self.assertEqual(
                transport.calls[0]["headers"]["openToken"],
                "stored-open-token",
            )

    def test_set_active_account_overrides_configured_default_account(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {"access_token": "open-token-a", "refresh_token": "refresh-token-a"},
            )
            token_store.save_token_response(
                "company-b",
                {"access_token": "open-token-b", "refresh_token": "refresh-token-b"},
            )
            settings = ChanjetSettings(
                app_key="app-key",
                app_secret="app-secret",
                active_account="company-a",
            )
            client, transport = self.make_client(
                [{"code": "0", "data": []}],
                settings=settings,
                token_store=token_store,
            )

            client.set_active_account("company-b")
            client.call_tplus_api("/tplus/api/v2/warehouse/Query")

            self.assertEqual(
                transport.calls[0]["headers"]["openToken"],
                "open-token-b",
            )

    def test_call_api_refreshes_missing_stored_open_token(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {"refresh_token": "stored-refresh-token"},
                make_active=True,
            )
            settings = ChanjetSettings(app_key="app-key", app_secret="app-secret")
            client, transport = self.make_client(
                [
                    {
                        "code": "200",
                        "result": {
                            "accessToken": "refreshed-open-token",
                            "refreshToken": "refreshed-refresh-token",
                            "expiresIn": 600,
                        },
                    },
                    {"code": "0", "data": []},
                ],
                settings=settings,
                token_store=token_store,
            )

            result = client.call_tplus_api(
                "/tplus/api/v2/warehouse/Query",
                body={"param": {"Code": "01"}},
                account_alias="company-a",
            )

            self.assertEqual(result, {"code": "0", "data": []})
            self.assertEqual(transport.calls[0]["url"], "https://openapi.chanjet.com/auth/token")
            self.assertEqual(transport.calls[0]["params"]["grant_type"], "refresh_token")
            self.assertEqual(
                transport.calls[1]["headers"]["openToken"],
                "refreshed-open-token",
            )
            self.assertEqual(
                token_store.get_account("company-a")["open_token"],
                "refreshed-open-token",
            )

    def test_call_api_refreshes_once_and_retries_expired_token_response(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {
                    "access_token": "expired-open-token",
                    "refresh_token": "stored-refresh-token",
                },
                make_active=True,
            )
            settings = ChanjetSettings(app_key="app-key", app_secret="app-secret")
            client, transport = self.make_client(
                [
                    {"code": "401", "message": "openToken expired"},
                    {
                        "code": "200",
                        "result": {
                            "accessToken": "refreshed-open-token",
                            "refreshToken": "refreshed-refresh-token",
                            "expiresIn": 600,
                        },
                    },
                    {"code": "0", "data": [{"Code": "01"}]},
                ],
                settings=settings,
                token_store=token_store,
            )

            result = client.call_tplus_api(
                "/tplus/api/v2/warehouse/Query",
                body={"param": {"Code": "01"}},
                account_alias="company-a",
            )

            self.assertEqual(result, {"code": "0", "data": [{"Code": "01"}]})
            self.assertEqual(
                transport.calls[0]["headers"]["openToken"],
                "expired-open-token",
            )
            self.assertEqual(transport.calls[1]["url"], "https://openapi.chanjet.com/auth/token")
            self.assertEqual(
                transport.calls[2]["headers"]["openToken"],
                "refreshed-open-token",
            )

    def test_call_api_does_not_retry_when_success_data_mentions_token_text(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            token_store = TokenStore(Path(tmp_dir) / "tokens.json")
            token_store.save_token_response(
                "company-a",
                {
                    "access_token": "open-token-a",
                    "refresh_token": "refresh-token-a",
                },
                make_active=True,
            )
            settings = ChanjetSettings(app_key="app-key", app_secret="app-secret")
            client, transport = self.make_client(
                [
                    {
                        "code": "0",
                        "data": {
                            "note": "the phrase openToken expired is only business data"
                        },
                    }
                ],
                settings=settings,
                token_store=token_store,
            )

            result = client.call_tplus_api("/tplus/api/v2/warehouse/Query")

            self.assertEqual(
                result,
                {
                    "code": "0",
                    "data": {
                        "note": "the phrase openToken expired is only business data"
                    },
                },
            )
            self.assertEqual(len(transport.calls), 1)
