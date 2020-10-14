# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# from urllib.parse import urlparse
# import mock
import json

from odoo import exceptions

from odoo.addons.website.tools import MockRequest

from .common import CommonCase


class DBLoggingCaseBase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_checkout")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.menu.picking_type_ids
        with cls.work_on_services(cls, menu=cls.menu, profile=cls.profile) as work:
            cls.service = work.component(usage="checkout")
        cls.log_model = cls.env["shopfloor.log"].sudo()

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"
        cls.picking = cls._create_picking()
        cls._fill_stock_for_moves(cls.picking.move_lines, in_package=True)
        cls.picking.action_assign()

    def _get_mocked_request(self, httprequest=None, extra_headers=None):
        mocked_request = MockRequest(self.env)
        # Make sure headers are there, no header in default mocked request :(
        headers = {
            "Cookie": "IaMaCookie!",
            "Api-Key": "I_MUST_STAY_SECRET",
        }
        headers.update(extra_headers or {})
        httprequest = httprequest or {}
        httprequest["headers"] = headers
        mocked_request.request["httprequest"] = httprequest
        return mocked_request


class DBLoggingCase(DBLoggingCaseBase):
    def test_no_log_entry(self):
        self.service._log_calls_in_db = False
        log_entry_count = self.log_model.search_count([])
        with self._get_mocked_request():
            resp = self.service.dispatch(
                "scan_document", params={"barcode": self.picking.name}
            )
        self.assertNotIn("log_entry_url", resp)
        self.assertFalse(self.log_model.search_count([]) > log_entry_count)

    def test_log_entry(self):
        log_entry_count = self.log_model.search_count([])
        with self._get_mocked_request():
            resp = self.service.dispatch(
                "scan_document", params={"barcode": self.picking.name}
            )
        self.assertIn("log_entry_url", resp)
        self.assertTrue(self.log_model.search_count([]) > log_entry_count)

    # TODO: this is very tricky because when the exception is raised
    # the transaction is explicitly rolled back and then our test env is gone
    # and everything right after is broken.
    # To fully test this we need a different test class setup and advanced mocking
    # and/or rewrite code so that we can it properly.
    # def test_log_exception(self):
    #     mock_path = \
    #         "odoo.addons.shopfloor.services.checkout.Checkout.scan_document"
    #     log_entry_count = self.log_model.search_count([])
    #     with self._get_mocked_request():
    #         with mock.patch(mock_path, autospec=True) as mocked:
    #             exc = exceptions.UserError("Sorry, you broke it!")
    #             mocked.side_effect = exc
    #             resp = self.service.dispatch(
    #                 "scan_document", params={"barcode": self.picking.name})
    #     self.assertIn("log_entry_url", resp)
    #     self.assertTrue(self.log_model.search_count([]) > log_entry_count)
    #     log_entry_data = urlparse(resp["log_entry_url"])
    #     pass

    def test_log_entry_values_success(self):
        _id = "whatever-id"
        params = {"barcode": self.picking.name}
        kw = {"result": {"data": "worked!"}}
        # test full data request only once, other tests will skip this part
        httprequest = {"url": "https://my.odoo.test/service/endpoint", "method": "POST"}
        extra_headers = {"KEEP-ME": "FOO"}
        with self._get_mocked_request(
            httprequest=httprequest, extra_headers=extra_headers
        ) as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, _id, params, **kw
            )
        expected = {
            "request_url": httprequest["url"],
            "request_method": httprequest["method"],
            "params": json.dumps(dict(params, _id=_id)),
            "headers": json.dumps(
                {"Cookie": "<redacted>", "Api-Key": "<redacted>", "KEEP-ME": "FOO"}
            ),
            "state": "success",
            "result": json.dumps({"data": "worked!"}),
            "error": False,
            "exception_name": False,
            "severity": False,
        }
        self.assertRecordValues(entry, [expected])

    def test_log_entry_values_failed(self):
        _id = "whatever-id"
        params = {"barcode": self.picking.name}
        # no result, will fail
        kw = {"result": {}}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, _id, params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": False,
            "exception_name": False,
            "severity": False,
        }
        self.assertRecordValues(entry, [expected])

    def _test_log_entry_values_failed_with_exception_default(self, severity=None):
        _id = "whatever-id"
        params = {"barcode": self.picking.name}
        fake_tb = """
            [...]
            File "/somewhere/in/your/custom/code/file.py", line 503, in write
            [...]
            ValueError: Ops, something went wrong
        """
        orig_exception = ValueError("Ops, something went wrong")
        kw = {"result": {}, "traceback": fake_tb, "orig_exception": orig_exception}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, _id, params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": fake_tb,
            "exception_name": "ValueError",
            "exception_message": "Ops, something went wrong",
            "severity": severity or "severe",
        }
        self.assertRecordValues(entry, [expected])

    def test_log_entry_values_failed_with_exception_default(self):
        self._test_log_entry_values_failed_with_exception_default()

    def test_log_entry_values_failed_with_exception_functional(self):
        _id = "whatever-id"
        params = {"barcode": self.picking.name}
        fake_tb = """
            [...]
            File "/somewhere/in/your/custom/code/file.py", line 503, in write
            [...]
            UserError: You are doing something wrong Dave!
        """
        orig_exception = exceptions.UserError("You are doing something wrong Dave!")
        kw = {"result": {}, "traceback": fake_tb, "orig_exception": orig_exception}
        with self._get_mocked_request() as mocked_request:
            entry = self.service._log_call_in_db(
                self.env, mocked_request, _id, params, **kw
            )
        expected = {
            "state": "failed",
            "result": "{}",
            "error": fake_tb,
            "exception_name": "odoo.exceptions.UserError",
            "exception_message": "You are doing something wrong Dave!",
            "severity": "functional",
        }
        self.assertRecordValues(entry, [expected])

        # test that we can still change severity as we like
        entry.severity = "severe"
        self.assertEqual(entry.severity, "severe")

    def test_log_entry_severity_mapping_param(self):
        # test override of mapping via config param
        mapping = self.log_model._get_exception_severity_mapping()
        self.assertEqual(mapping, self.log_model.EXCEPTION_SEVERITY_MAPPING)
        self.assertEqual(mapping["ValueError"], "severe")
        self.assertEqual(mapping["odoo.exceptions.UserError"], "functional")
        value = "ValueError: warning, odoo.exceptions.UserError: severe"
        self.env["ir.config_parameter"].sudo().create(
            {"key": "shopfloor.log.severity.exception.mapping", "value": value}
        )
        mapping = self.log_model._get_exception_severity_mapping()
        self.assertEqual(mapping["ValueError"], "warning")
        self.assertEqual(mapping["odoo.exceptions.UserError"], "severe")
        self._test_log_entry_values_failed_with_exception_default("warning")

    def test_log_entry_severity_mapping_param_bad_values(self):
        # bad values are discarded
        value = """
            ValueError: warning,
            odoo.exceptions.UserError::badvalue,
            VeryBadValue|error
        """
        self.env["ir.config_parameter"].sudo().create(
            {"key": "shopfloor.log.severity.exception.mapping", "value": value}
        )
        mapping = self.log_model._get_exception_severity_mapping()
        expected = self.log_model.EXCEPTION_SEVERITY_MAPPING.copy()
        expected["ValueError"] = "warning"
        self.assertEqual(mapping, expected)
