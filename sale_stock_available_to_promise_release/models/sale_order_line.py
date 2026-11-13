# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    availability_status = fields.Selection(
        selection=[
            ("on_order", "On order"),
            ("full", "Fully Available"),
            ("partial", "Partially Available"),
            ("restock", "Restock ordered"),
            ("no", "Not available"),
        ],
        compute="_compute_availability_status",
    )
    expected_availability_date = fields.Datetime(compute="_compute_availability_status")
    available_qty = fields.Float(
        digits="Product Unit of Measure", compute="_compute_availability_status"
    )
    delayed_qty = fields.Float(
        digits="Product Unit of Measure", compute="_compute_availability_status"
    )

    @api.depends(
        "move_ids.ordered_available_to_promise_uom_qty",
        "move_ids.need_release",
        "move_ids.product_uom",
        "move_ids.picking_id.last_release_date",
        "move_ids.product_uom_qty",
        "move_ids.reserved_availability",
        "move_ids.state",
        "product_uom",
        "product_id.route_ids",
        "route_id",
        "product_uom_qty",
        "display_type",
        "is_delivery",
    )
    def _compute_availability_status(self):
        for record in self:
            data = record._get_availability_data()
            record.update(data)

    def _get_availability_data(self):
        data = dict.fromkeys(
            (
                "availability_status",
                "expected_availability_date",
                "available_qty",
                "delayed_qty",
            ),
            False,
        )
        self.ensure_one()
        required_qty = self._get_availability_required_qty()
        if self.display_type or not self.product_id:
            return data
        elif self.is_delivery:
            data["availability_status"] = "full"
            data["available_qty"] = required_qty
            return data
        product = self.product_id
        # Fallback values
        availability_status = "no"
        expected_availability_date = False
        # Get availabile qty as sale order line's UOM.
        available_qty = self._get_available_qty()
        delayed_qty = 0
        # required values
        rounding = self.product_uom.rounding
        # Fully available
        if (
            product.type == "service"
            or float_compare(available_qty, required_qty, precision_rounding=rounding)
            >= 0
        ):
            availability_status = "full"
            available_qty = required_qty
        # Partially available
        elif float_compare(available_qty, 0, precision_rounding=rounding) == 1:
            availability_status = "partial"
            delayed_qty = required_qty - available_qty
        # On order product
        elif self._on_order_route():
            availability_status = "on_order"
        # No stock
        elif float_is_zero(available_qty, precision_rounding=rounding):
            product_replenishment_date = product._get_next_replenishment_date()
            # Replenishment ordered
            if product_replenishment_date:
                availability_status = "restock"
                expected_availability_date = product_replenishment_date
                delayed_qty = required_qty
        return {
            "availability_status": availability_status,
            "expected_availability_date": expected_availability_date,
            "available_qty": available_qty,
            "delayed_qty": delayed_qty,
        }

    def _get_availability_required_qty(self):
        """return the quantity against which availability is evaluated"""
        self.ensure_one()
        return self.product_uom_qty

    def _get_availability_moves(self):
        """return the stock moves contributing to availability"""
        self.ensure_one()
        return self.move_ids.filtered(lambda move: move.state != "cancel")

    def _get_available_qty(self):
        """return available stock in the sale line unit of measure"""
        self.ensure_one()
        available_qty = 0
        for move in self._get_availability_moves():
            available_qty += move.product_uom._compute_quantity(
                self._get_availability_move_qty(move),
                self.product_uom,
                rounding_method="HALF-UP",
            )
        return available_qty

    def _get_availability_move_qty(self, move):
        """return the contributing quantity in the move unit of measure"""
        if move.need_release:
            return move.ordered_available_to_promise_uom_qty
        if move.picking_id.last_release_date:
            return move.product_uom_qty
        return move.reserved_availability

    def _on_order_route(self):
        self.ensure_one()
        return self.is_mto
