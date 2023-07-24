# Copyright 2022 Camptocamp SA
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.exceptions import UserError

from odoo.addons.stock_warehouse_flow.tests import common


class TestWarehouseFlow(common.CommonFlow):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.packaging_type = cls.env.ref(
            "product_packaging_type.product_packaging_type_default"
        )
        cls.packaging_type.sequence = 100
        cls.packaging_type_2 = cls.env["product.packaging.type"].create(
            {"name": "Test", "code": "Test", "sequence": 1}
        )

    def test_flow_uniq_constraint(self):
        flow = self._get_flow("pick_ship")
        vals = flow.copy_data()[0]
        with self.assertRaises(UserError):
            vals["carrier_ids"] = [
                (6, 0, self.env.ref("delivery.delivery_carrier").ids)
            ]
            self.env["stock.warehouse.flow"].create(vals)

    def test_flow_uniq_constraint_types(self):
        flow = self._get_flow("pick_ship")
        flow.packaging_type_ids = self.packaging_type
        vals = flow.copy_data()[0]
        self.env["stock.warehouse.flow"].create(vals)
        with self.assertRaises(UserError):
            vals["packaging_type_ids"] = [(6, 0, self.packaging_type.ids)]
            self.env["stock.warehouse.flow"].create(vals)

    def _prepare_split_test(self):
        self.product.packaging_ids = [
            (
                0,
                0,
                {
                    "name": "Test Pack",
                    "qty": 4,
                    "packaging_type_id": self.packaging_type_2.id,
                },
            ),
            (
                0,
                0,
                {
                    "name": "Split Pack",
                    "qty": 4,
                    "packaging_type_id": self.packaging_type.id,
                },
            ),
        ]
        ship_flow = self._get_flow("ship_only")
        ship_flow.sequence = 100
        pick_flow = self._get_flow("pick_ship")
        pick_flow.write(
            {
                "sequence": 1,
                "packaging_type_ids": [(6, 0, self.packaging_type.ids)],
                "split_method": "packaging",
                "carrier_ids": [(6, 0, ship_flow.carrier_ids.ids)],
            }
        )
        return ship_flow, pick_flow

    def _run_split_flow(self):
        pick_flow = self._get_flow("pick_ship")
        moves_before = self.env["stock.move"].search([])
        self._run_procurement(self.product, 5, pick_flow.carrier_ids)
        moves_after = self.env["stock.move"].search([])
        return (moves_after - moves_before).sorted(lambda m: m.id)

    def test_split(self):
        self._prepare_split_test()
        moves = self._run_split_flow()
        self.assertEqual(moves.mapped("product_qty"), [4, 1, 4])
        self.assertEqual(
            moves.mapped("picking_type_id.code"), ["outgoing", "outgoing", "internal"]
        )

    def test_split_no_flow_for_split_move(self):
        ship_flow, pick_flow = self._prepare_split_test()
        ship_flow.unlink()
        with self.assertRaises(UserError):
            self._run_split_flow()
