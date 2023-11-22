# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestSetPackDimension(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # Activate the option to use the module
        cls.menu.sudo().set_packaging_dimension = True
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        # Picking has 3 products
        # Product A with one packaging
        # Product B with no packaging
        cls.product_b.packaging_ids = [(5, 0, 0)]
        # Product C with 2 packaging
        cls.product_c_packaging_2 = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Big Box",
                    "product_id": cls.product_c.id,
                    "barcode": "ProductCBigBox",
                    "qty": 6,
                }
            )
        )

        cls.line_with_packaging = cls.picking.move_line_ids[0]
        cls.line_without_packaging = cls.picking.move_line_ids[1]

    def _assert_response_set_dimension(
        self, response, picking, line, packaging, message=None
    ):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_line(line),
            "packaging": self.data_detail.packaging_detail(packaging),
        }
        self.assert_response(
            response,
            next_state="set_packaging_dimension",
            data=data,
            message=message,
        )

    def test_scan_product_ask_for_dimension(self):
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
        self._assert_response_set_dimension(
            response, self.picking, selected_move_line, self.product_a_packaging
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
        self._assert_response_set_dimension(
            response, self.picking, selected_move_line, self.product_a_packaging
        )

    def test_set_packaging_dimension(self):
        selected_move_line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        self.service.dispatch(
            "set_packaging_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": selected_move_line.id,
                "packaging_id": self.product_a_packaging.id,
                "height": 55,
                "qty": 34,
                "barcode": "barcode",
            },
        )
        self.assertEqual(self.product_a_packaging.height, 55)
        self.assertEqual(self.product_a_packaging.barcode, "barcode")
        self.assertEqual(self.product_a_packaging.qty, 34)

    def test_set_multiple_packaging_dimension(self):
        line = self.picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_c
        )
        # Set the weight but other dimension are required
        self.product_c_packaging_2.max_weight = 200
        response = self.service.dispatch(
            "set_packaging_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "packaging_id": self.product_c_packaging.id,
                "height": 55,
                "length": 233,
            },
        )
        self.assertEqual(self.product_c_packaging.height, 55)
        self.assertEqual(self.product_c_packaging.packaging_length, 233)
        self._assert_response_set_dimension(
            response,
            self.picking,
            line,
            self.product_c_packaging_2,
            message=self.msg_store.packaging_dimension_updated(
                self.product_c_packaging
            ),
        )
        response = self.service.dispatch(
            "set_packaging_dimension",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": line.id,
                "packaging_id": self.product_c_packaging_2.id,
                "height": 200,
                "max_weight": 1000,
            },
        )
        self.assertEqual(self.product_c_packaging_2.height, 200)
        self.assertEqual(self.product_c_packaging_2.max_weight, 1000)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_lines(line),
                "confirmation_required": None,
            },
            message=self.msg_store.packaging_dimension_updated(
                self.product_c_packaging_2
            ),
        )
