# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopfloor.tests.test_zone_picking_base import ZonePickingCommonCase


# pylint: disable=missing-return
class ZonePickingLossQuantityStockIssueCase(ZonePickingCommonCase):
    """Test /stock_issue with the `loss_quantity` stock issue strategy."""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.menu.sudo().stock_issue_strategy = "loss_quantity"
        cls.wh.sudo().use_loss_picking = True

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_stock_issue_declares_a_loss(self):
        """Declaring a stock issue locks the quant behind a move of the
        warehouse's Loss operation type, instead of silently correcting
        the inventory count.
        """
        move_line = self.picking1.move_line_ids[0]
        move = move_line.move_id
        product = move.product_id
        location = move_line.location_id
        package = move_line.package_id

        self.service.dispatch(
            "stock_issue",
            params={"move_line_id": move_line.id},
        )

        quant = self.env["stock.quant"]._gather(
            product, location, package_id=package, strict=True
        )
        self.assertTrue(quant.is_locked_by_picking)
        loss_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", self.wh.loss_type_id.id)]
        )
        self.assertEqual(len(loss_picking), 1)
        self.assertEqual(loss_picking.move_ids.quant_lock_quant_id, quant)
