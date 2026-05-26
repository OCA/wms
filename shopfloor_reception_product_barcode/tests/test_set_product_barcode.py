# Copyright 2023 Camptocamp SA
# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.shopfloor_reception.tests.common import CommonCase

from ..hooks import post_init_hook, uninstall_hook


class TestSetProductDimension(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()
        # Activate the option to use the module
        cls.menu.sudo().set_product_barcode = True
        cls.picking_type.sudo().use_create_lots = True
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        return res

    def _assert_response_set_barcode(
        self, response, picking, line, barcode, message=None
    ):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_line(line),
            "product": self.data_detail.product_detail(line.product_id),
            "product_barcode": barcode,
        }
        self.assert_response(
            response,
            next_state="set_product_barcode",
            data=data,
            message=message,
        )

    def _assert_response_updated_set_quantity(
        self, response, picking, line, message=None
    ):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": [self.data.move_line(line)],
            "confirmation_required": None,
        }
        self.assert_response(
            response,
            next_state="set_quantity",
            data=data,
            message=message,
        )

    def test_hooks(self):
        post_init_hook(self.env.cr, self.env.registry)
        scenario = self.env.ref("shopfloor_reception.scenario_reception")
        self.assertTrue(scenario.options.get("set_product_barcode"))

        self.assertTrue(self.menu.set_product_barcode_is_possible)

        uninstall_hook(self.env.cr, self.env.registry)
        self.assertNotIn(
            "set_product_barcode",
            scenario.options,
        )

    def test_scan_product_ask_for_barcode(self):
        """
        Check we ask for a barcode if product's one is empty

        We check also the barcode scan
        """
        self.product_a.barcode = ""
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": self.picking.id,
                "barcode": self.product_a.default_code,
            },
        )
        self.data.picking(self.picking)
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._assert_response_set_barcode(
            response, self.picking, selected_move_line, ""
        )

        # Check the response for barcode scan
        response = self.service.dispatch(
            "set_product_barcode_scan",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "0799439112766",
            },
        )
        self._assert_response_set_barcode(
            response, self.picking, selected_move_line, "0799439112766"
        )

    def test_scan_product_dont_ask_for_barcode(self):
        """
        Product has already a barcode, don't ask
        """
        self.product_a.tracking = "none"
        # self._add_package(self.picking)
        self.assertTrue(self.product_a.packaging_ids)
        response = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": self.picking.id,
                "barcode": self.product_a.barcode,
            },
        )
        self.data.picking(self.picking)
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._assert_response_updated_set_quantity(
            response, self.picking, selected_move_line
        )

    def test_scan_lot_ask_for_barcode(self):
        self.product_a.tracking = "none"
        self.product_a.barcode = ""
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": "Test Lot",
            },
        )
        self.data.picking(self.picking)
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._assert_response_set_barcode(
            response, self.picking, selected_move_line, ""
        )

    def test_set_product_barcode(self):
        self.product_a.barcode = ""
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.service.dispatch(
            "set_product_barcode",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
                "barcode": "0799439112766",
            },
        )
        self.assertEqual(self.product_a.barcode, "0799439112766")

    def test_set_multiple_product_barcode(self):
        line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_c
        )
        self.product_c.barcode = ""
        response = self.service.dispatch(
            "set_product_barcode",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "barcode": "0000000000",
            },
        )
        self.assertEqual(self.product_c.barcode, "0000000000")
        self._assert_response_updated_set_quantity(
            response,
            self.picking,
            line,
            message=self.msg_store.product_barcode_updated(self.product_c),
        )

        response = self.service.dispatch(
            "set_product_barcode",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "barcode": "00000000112",
            },
        )
        self.assertEqual(self.product_c.barcode, "0000000000")
        self._assert_response_updated_set_quantity(
            response,
            self.picking,
            line,
        )
