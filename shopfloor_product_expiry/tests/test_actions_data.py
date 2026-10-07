# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
# pylint: disable=missing-return

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class ActionsDataCase(ActionsDataCaseBase):
    def test_data_move_line_expiration_date(self):
        product = (
            self.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product with expiration",
                    "type": "product",
                    "tracking": "lot",
                    "use_expiration_date": True,
                    "barcode": "TEST",
                    "default_code": "test",
                }
            )
        )
        # Create a new move line
        move_line = self.env["stock.move.line"].create(
            {
                "picking_id": self.move_b.picking_id.id,
                "product_id": product.id,
                "qty_done": 5.0,
                "expiration_date": "2022-07-01",
            }
        )
        data = self.data.move_line(move_line, expiration_date=True)
        self.assert_schema(self.schema.move_line(), data)
        expected = {
            "expiration_date": "2022-07-01T00:00:00",
        }
        self.assertDictContainsSubset(expected, data)

    def test_data_lot_expiry(self):
        lot = self.env["stock.lot"].create(
            {
                "product_id": self.product_a.id,
                "expiration_date": "2022-07-01",
                "removal_date": "2022-08-01",
            }
        )
        data = self.data_detail.lot_detail(lot)
        expected = {
            "expiration_date": "2022-07-01T00:00:00",
            "removal_date": "2022-08-01T00:00:00",
        }
        self.assertDictContainsSubset(expected, data)
