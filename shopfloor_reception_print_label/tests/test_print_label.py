# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from contextlib import contextmanager
from unittest import mock

from odoo.modules.module import get_resource_path
from odoo.tools import convert_file

from odoo.addons.base_report_to_printer.models.ir_actions_report import IrActionsReport
from odoo.addons.component.core import WorkContext
from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestSetDestinationPrinting(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with cls._work_on_services(cls, menu=cls.menu) as work:
            cls.reception = work.component(usage="reception")

        this_module = "shopfloor_reception_print_label"
        convert_file(
            cls.env.cr,
            "shopfloor_reception_print_label",
            get_resource_path(this_module, "tests/report.xml"),
            {},
            mode="init",
            noupdate=False,
            kind="test",
        )

    @contextmanager
    def _work_on_services(self, collection=None, env=None, **params):
        collection = collection or self.shopfloor_app
        if env:
            collection = collection.with_env(env)
        params = params or {}
        yield WorkContext(
            collection=collection,
            # No need for a real request mock
            # as we don't deal w/ real request for testing
            # but base_rest context provider needs it.
            request=mock.Mock(),
            **params
        )

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.location_dest = cls.env.ref("stock.stock_location_stock")

    def test_print_labels(self):
        report = self.env.ref("shopfloor_reception_print_label.report_test_document")
        self.reception.work.menu.sudo().label_print_report_id = report
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        with mock.patch.object(
            IrActionsReport, "print_document_client_action"
        ) as mock_print:
            mock_print.return_value = True
            response = self.reception.dispatch(
                "print_labels",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "quantity": 2,
                },
            )
            mock_print.assert_called_once()
            message = {"message_type": "success", "body": "Print job sent"}
            self.assertEqual(
                message,
                message | response.get("message"),
            )

    def test_print_labels_error(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        with mock.patch.object(
            IrActionsReport, "print_document_client_action"
        ) as mock_print:
            mock_print.return_value = False
            response = self.service.dispatch(
                "print_labels",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "quantity": 2,
                },
            )
            mock_print.assert_not_called()
            message = {
                "message_type": "warning",
                "body": "No report found to be printed. Check your scenario menu "
                "configuration with your Administrator!",
            }
            self.assertEqual(
                message,
                message | response.get("message"),
            )
