# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class ActionsDataPurchase(ActionsDataCaseBase):
    def test_data_purchase_order(self):
        picking = self.env["stock.picking"].search(
            [("purchase_id", "!=", False)], limit=1
        )
        purchase = picking.purchase_id
        purchase.sudo().partner_ref = "test"
        expected_purchase_data = {
            "id": purchase.id,
            "name": purchase.name,
            "partner_ref": purchase.partner_ref,
        }
        purchase_data = self.data.purchase_order(purchase)
        self.assertDictEqual(expected_purchase_data, purchase_data)
        self.assert_schema(self.schema.purchase_order(), purchase_data)
        data = self.data.picking(picking)
        self.assertTrue("purchase_order" not in data)
        expected_picking_data = data
        expected_picking_data.update({"purchase_order": purchase_data})
        self.assert_schema(self.schema.picking(), expected_picking_data)
        self.assertDictEqual(
            expected_picking_data,
            self.data.picking(picking, with_purchase_order=True),
        )
