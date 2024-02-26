# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command

from odoo.addons.stock_release_channel_block_backorder.tests import common


class TestSaleStockPicking(common.CommonReleaseChannelBlock):
    @classmethod
    def _create_order(cls, product_qty):
        return cls.env["sale.order"].create(
            {
                "partner_id": cls.partner.id,
                "order_line": [
                    Command.create(
                        {
                            "name": cls.product.name,
                            "product_id": cls.product.id,
                            "product_uom_qty": product_qty,
                        },
                    )
                ],
            }
        )

    def test_06(self):
        """Users can prevent a sale order from being delivered individually."""
        sale = self._create_order(product_qty=20)
        sale.do_not_deliver_if_alone = True
        sale.action_confirm()
        picking = sale.picking_ids
        self.assertTrue(picking.move_ids.delivery_requires_other_lines)
        self.assertTrue(picking.delivery_requires_other_lines)
        picking.assign_release_channel()
        self.assertFalse(picking.release_channel_id)
