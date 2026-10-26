# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from contextlib import contextmanager
from unittest import mock

from odoo_test_helper.fake_model_loader import FakeModelLoader

from odoo.modules.module import get_resource_path
from odoo.tools import convert_file

from odoo.addons.base_report_to_printer.models.printing_printer import PrintingPrinter
from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext
from odoo.addons.shopfloor_base.tests.common import CommonCase as BaseCommonCase


class TestPrinting(BaseCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        printer_server = cls.env["printing.server"].sudo().create({})
        cls.printer = (
            cls.env["printing.printer"]
            .sudo()
            .create(
                {
                    "name": "TEST",
                    "system_name": "TEST",
                    "server_id": printer_server.id,
                }
            )
        )
        cls.env.user.printing_printer_id = cls.printer
        cls.menu = cls.env.ref("shopfloor_base.shopfloor_menu_demo_1")
        from .models import (
            ShopFloorPrintingAction,
            ShopfloorTestFlow,
            ShopfloorTestValidator,
        )

        ShopFloorPrintingAction._build_component(cls._components_registry)
        ShopfloorTestFlow._build_component(cls._components_registry)
        ShopfloorTestValidator._build_component(cls._components_registry)

        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()

        # The fake class is imported here !! After the backup_registry
        from .models import ShopfloorTestModel

        cls.loader.update_registry((ShopfloorTestModel,))
        this_module = "shopfloor_printing_base"
        convert_file(
            cls.env.cr,
            "shopfloor_printing_base",
            get_resource_path(this_module, "tests/report.xml"),
            {},
            mode="init",
            noupdate=False,
            kind="test",
        )
        convert_file(
            cls.env.cr,
            "shopfloor_printing_base",
            get_resource_path(this_module, "tests/access.xml"),
            {},
            mode="init",
            noupdate=False,
            kind="test",
        )

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        super().tearDownClass()

    @contextmanager
    def _work_on_actions(self, **params):
        params = params or {}
        collection = _PseudoCollection("shopfloor.action", self.env)
        yield WorkContext(
            model_name="shopfloor.test.model",
            components_registry=self._components_registry,
            collection=collection,
            **params
        )

    def setUp(self):
        super().setUp()
        # Get a base scenario
        with self._work_on_actions(menu=self.menu) as work_action:
            self.service = work_action.component(usage="test")
        self.test_record = self.env["shopfloor.test.model"].sudo().create({})

    def test_print_no_report(self):
        with mock.patch.object(PrintingPrinter, "print_document") as mock_print:
            printing = self.service._printing_for("test")
            mock_print.return_value = False
            response = printing.print(
                record_ids=self.test_record.ids,
                quantity=1,
            )
            mock_print.assert_not_called()
            self.assertDictEqual(
                {
                    "message_type": "warning",
                    "body": "No report found to be printed. Check your "
                    "scenario menu configuration with your Administrator!",
                },
                response,
            )

    def test_print_report(self):
        self.service.work.menu.sudo().label_print_report_id = self.env.ref(
            "shopfloor_printing_base.report_test_document"
        )
        with mock.patch.object(PrintingPrinter, "print_document") as mock_print:
            printing = self.service._printing_for("test")

            # Document is printed
            mock_print.return_value = True
            response = printing.print(
                record_ids=self.test_record.ids,
                quantity=1,
            )
            mock_print.assert_called()
            self.assertDictEqual(
                {"message_type": "success", "body": "Print job sent"},
                response,
            )

    def test_print_report_error(self):
        self.service.work.menu.sudo().label_print_report_id = self.env.ref(
            "shopfloor_printing_base.report_test_document"
        )
        with mock.patch.object(PrintingPrinter, "print_document") as mock_print:
            printing = self.service._printing_for("test")

            # Document is not printed
            mock_print.return_value = False
            response = printing.print(
                record_ids=self.test_record.ids,
                quantity=1,
            )
            mock_print.assert_called()
            self.assertDictEqual(
                {"message_type": "warning", "body": "Printing error"},
                response,
            )

    def test_response(self):
        self.service.work.menu.sudo().display_print_label_button = True
        response = self.service._response(data={"id": id})
        allow = response.get("data", {}).get("allow_print_label")
        self.assertTrue(allow)
