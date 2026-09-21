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
        cls.menu.sudo().set_product_dimension = True
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        return res

    def _assert_response_set_dimension(self, response, picking, line, message=None):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_line(line),
            "product": self.data_detail.product_detail(line.product_id),
        }
        self.assert_response(
            response,
            next_state="set_product_dimension",
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
        self.assertTrue(scenario.options.get("set_product_dimension"))

        self.assertTrue(self.menu.set_product_dimension_is_possible)

        uninstall_hook(self.env.cr, self.env.registry)
        self.assertNotIn(
            "set_product_dimension",
            scenario.options,
        )

    def test_scan_product_ask_for_dimension(self):
        self.product_a.tracking = "none"
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
        self._assert_response_set_dimension(response, self.picking, selected_move_line)

    def test_scan_product_dont_ask_for_dimension(self):
        self.product_a.tracking = "none"
        self.product_a.update(
            {
                "product_height": 10.0,
                "product_length": 10.0,
                "product_width": 10.0,
                "weight": 2.0,
            }
        )
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
            response,
            self.picking,
            selected_move_line,
        )

    def test_scan_lot_ask_for_dimension(self):
        self.product_a.tracking = "none"
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.assertTrue(self.product_a.packaging_ids)
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
            },
        )
        self.data.picking(self.picking)
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self._assert_response_set_dimension(response, self.picking, selected_move_line)

    def test_set_product_dimension(self):
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.service.dispatch(
            "set_product_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
                "height": 55,
            },
        )
        self.assertEqual(self.product_a.product_height, 55)

    def test_set_multiple_product_dimension(self):
        line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_c
        )
        # Set the weight but other dimension are required
        self.product_c.weight = 200
        response = self.service.dispatch(
            "set_product_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "height": 55,
                "length": 233,
                "weight": 12.5,
            },
        )
        self.assertEqual(self.product_c.product_height, 55)
        self.assertEqual(self.product_c.product_length, 233)
        self.assertEqual(self.product_c.weight, 12.5)
        self._assert_response_updated_set_quantity(
            response,
            self.picking,
            line,
            message=self.msg_store.product_dimension_updated(self.product_c),
        )
        response = self.service.dispatch(
            "set_product_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "height": 200,
            },
        )
        self.assertEqual(self.product_c.product_height, 200)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(line),
                "confirmation_required": None,
            },
            message=self.msg_store.product_dimension_updated(self.product_c),
        )
