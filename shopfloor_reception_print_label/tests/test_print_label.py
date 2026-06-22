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
            model_name=collection._name,
            collection=collection,
            # No need for a real request mock
            # as we don't deal w/ real request for testing
            # but base_rest context provider needs it.
            request=mock.Mock(),
            **params,
        )

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        cls.location_dest = cls.env.ref("stock.stock_location_stock")

    def test_print_labels_no_report_error(self):
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

            self.assertMessage(response, self.msg_store.print_no_report())

    def test_print_labels_supported_models(self):
        report = self.env.ref("shopfloor_reception_print_label.report_test_document")
        self.reception.work.menu.sudo().label_print_report_id = report
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # Ensure a lot exists on the move line for the lot test
        lot = self.env["stock.lot"].create(
            {
                "name": "Test Lot",
                "product_id": self.product_a.id,
                "company_id": picking.company_id.id,
            }
        )
        selected_move_line.lot_id = lot

        models_to_test = [
            ("stock.move.line", selected_move_line.ids),
            ("stock.picking", picking.ids),
            ("product.product", self.product_a.ids),
            ("product.template", self.product_a.product_tmpl_id.ids),
            ("stock.lot", lot.ids),
        ]

        for model, expected_ids in models_to_test:
            with self.subTest(model=model):
                report.sudo().model = model
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
                    mock_print.assert_called_once_with(expected_ids, **{"quantity": 2})
                    message = {"message_type": "success", "body": "Print job sent"}
                    self.assertMessage(response, message)

    def test_print_labels_lot_missing_error(self):
        report = self.env.ref("shopfloor_reception_print_label.report_test_document")
        report.sudo().model = "stock.lot"
        self.reception.work.menu.sudo().label_print_report_id = report
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.lot_id = False  # Ensure no lot is defined

        response = self.reception.dispatch(
            "print_labels",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 2,
            },
        )
        self.assert_response(
            response,
            next_state="set_destination",
            message=self.msg_store.lot_report_but_no_lot_defined(),
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self._data_for_move_lines(selected_move_line),
                "confirmation": None,
            },
        )

    def test_print_labels_unsupported_model_error(self):
        report = self.env.ref("shopfloor_reception_print_label.report_test_document")
        report.sudo().model = "res.partner"  # Unsupported model
        self.reception.work.menu.sudo().label_print_report_id = report
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )

        response = self.reception.dispatch(
            "print_labels",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "quantity": 2,
            },
        )
        self.assert_response(
            response,
            next_state="set_destination",
            message=self.msg_store.report_model_unsupported(
                self.menu.label_print_report_id
            ),
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self._data_for_move_lines(selected_move_line),
                "confirmation": None,
            },
        )

    def test_set_quantity_auto_print_labels(self):
        self.reception.work.menu.sudo().write(
            {
                "auto_print_labels_on_location_scan": True,
                "label_print_report_id": self.env.ref(
                    "shopfloor_reception_print_label.report_test_document"
                ).id,
            }
        )
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid

        with mock.patch.object(
            IrActionsReport, "print_document_client_action"
        ) as mock_print:
            mock_print.return_value = True
            self.service.dispatch(
                "set_quantity",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "barcode": self.dispatch_location.barcode,
                    "quantity": 1,
                },
            )
            mock_print.assert_called_once_with(
                selected_move_line.ids, **{"quantity": 1}
            )
