# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.addons.shopfloor.tests.test_location_content_transfer_base import (
    LocationContentTransferCommonCase,
)


# pylint: disable=missing-return
class LocationContentTransferLossQuantityStockOutCase(
    LocationContentTransferCommonCase
):
    """Test /stock_out_package with the `loss_quantity` stock issue strategy."""

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.menu.sudo().stock_issue_strategy = "loss_quantity"
        cls.wh.sudo().use_loss_picking = True
        cls.picking1 = cls._create_picking(lines=[(cls.product_a, 10)])
        cls._fill_stock_for_moves(
            cls.picking1.move_ids, in_package=True, location=cls.content_loc
        )
        cls.picking1.action_assign()

    def _assert_loss_declared(self, product, location, package):
        quant = self.env["stock.quant"]._gather(
            product, location, package_id=package, strict=True
        )
        self.assertTrue(quant.is_locked_by_picking)
        loss_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", self.wh.loss_type_id.id)]
        )
        self.assertEqual(len(loss_picking), 1)
        self.assertEqual(loss_picking.move_ids.quant_lock_quant_id, quant)

    def test_stock_out_package_declares_a_loss_when_move_is_canceled(self):
        """The move is ad-hoc (created by the current user): it is canceled
        outright, but a loss must still be declared for the location so the
        stock issue strategy is honored the same way as for other moves.
        """
        move = self.picking1.move_ids
        package_level = self.picking1.move_line_ids.package_level_id
        product = move.product_id
        location = self.content_loc
        package = package_level.package_id

        self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": location.id,
                "package_level_id": package_level.id,
            },
        )

        self.assertEqual(move.state, "cancel")
        self._assert_loss_declared(product, location, package)

    def test_stock_out_package_declares_a_loss_when_lines_not_owned(self):
        """The move is not owned by the current user: it is unreserved, and
        a loss must be declared for the location.
        """
        self.env.user = self.shopfloor_manager
        self.assertTrue(self.env.user != self.picking1.create_uid)
        move = self.picking1.move_ids
        package_level = self.picking1.move_line_ids.package_level_id
        product = move.product_id
        location = self.content_loc
        package = package_level.package_id

        self.service.dispatch(
            "stock_out_package",
            params={
                "location_id": location.id,
                "package_level_id": package_level.id,
            },
        )

        self._assert_loss_declared(product, location, package)
