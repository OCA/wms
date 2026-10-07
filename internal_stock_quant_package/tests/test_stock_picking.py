# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.exceptions import UserError
from odoo.fields import Command

from .common import TestStockPickingInternal


class TestStockPickingInternalFlow(TestStockPickingInternal):
    def test_internal_result_package_emptied_on_transfer(self):
        self.assertEqual(self.picking.state, "assigned")
        packop = self.picking.move_line_ids
        packop.write(
            dict(
                result_package_id=self.internal_package.id,
                qty_done=packop.reserved_qty,
            )
        )
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertFalse(self.internal_package.quant_ids)

    def test_internal_result_package_not_emptied_on_transfer(self):
        self.picking_type_out.empty_internal_package_on_transfer = False
        self.assertEqual(self.picking.state, "assigned")
        packop = self.picking.move_line_ids
        packop.write(
            dict(
                result_package_id=self.internal_package.id,
                qty_done=packop.reserved_qty,
            )
        )
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertTrue(self.internal_package.quant_ids)

    def test_external_package_not_emptied_on_transfer(self):
        self.assertEqual(self.picking.state, "assigned")
        packop = self.picking.move_line_ids
        packop.write(
            dict(
                result_package_id=self.external_package.id,
                qty_done=packop.reserved_qty,
            )
        )
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertTrue(self.external_package.quant_ids)

    def test_internal_package_emptied_on_put_in_pack(self):
        self.assertEqual(self.picking.state, "assigned")
        packop = self.picking.move_line_ids
        packop.write(
            dict(
                result_package_id=self.internal_package.id,
                qty_done=packop.reserved_qty,
            )
        )
        self.picking.action_put_in_pack()
        self.assertNotEqual(packop.result_package_id, self.internal_package)
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertFalse(self.internal_package.quant_ids)

    def test_internal_package_not_emptied_on_put_in_pack(self):
        self.picking_type_out.empty_internal_package_on_transfer = False
        self.assertEqual(self.picking.state, "assigned")
        packop = self.picking.move_line_ids
        packop.write(
            dict(
                result_package_id=self.internal_package.id,
                qty_done=packop.reserved_qty,
            )
        )
        msg = "Please add 'Done' quantities to the picking to create a new pack."
        with self.assertRaises(UserError, msg=msg):
            self.picking.action_put_in_pack()
        self.equal = self.assertEqual(packop.result_package_id, self.internal_package)
        self.picking.button_validate()
        self.assertEqual(self.picking.state, "done")
        self.assertTrue(self.internal_package.quant_ids)

    def test_internal_package_emptied_on_transfer_depend_on_carrier(self):
        carrier_product = self.env["product.product"].create(
            {"name": "Product Carrier", "sale_ok": False, "type": "service"}
        )
        carrier_1 = self.env["delivery.carrier"].create(
            {
                "name": "Carrier1",
                "product_id": carrier_product.id,
            }
        )
        self.picking.carrier_id = carrier_1
        vals_line = {"empty": False, "delivery_carrier_id": carrier_1.id}
        vals = {"stock_internal_package_config_line_ids": [Command.create(vals_line)]}
        self.picking_type_out.write(vals)

        self.assertFalse(self.picking.empty_internal_package_on_transfer)

        line = self.picking_type_out.stock_internal_package_config_line_ids
        line.empty = True

        self.assertTrue(self.picking.empty_internal_package_on_transfer)
