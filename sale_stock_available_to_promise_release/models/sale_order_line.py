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

    def _on_order_route(self):
        self.ensure_one()
        mto_route = self.env.ref("stock.route_warehouse0_mto")
        product_is_mto = mto_route in self.product_id.route_ids
        line_is_mto = mto_route == self.route_id
        return product_is_mto or line_is_mto

    @api.depends(
        "move_ids.ordered_available_to_promise_uom_qty",
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
            ("availability_status", "expected_availability_date", "available_qty"),
            False,
        )
        self.ensure_one()
        if self.display_type or not self.product_id:
            return data
        elif self.is_delivery:
            data["availability_status"] = "full"
            data["available_qty"] = self.product_uom_qty
            return data
        # Fallback values
        availability_status = "no"
        expected_availability_date = False
        available_qty = sum(
            self.mapped("move_ids.ordered_available_to_promise_uom_qty")
        )
        # required values
        product = self.product_id
        rounding = product.uom_id.rounding
        # on_order product
        if self._on_order_route():
            availability_status = "on_order"
        # Fully available
        elif (
            product.type == "service"
            or float_compare(
                available_qty, self.product_uom_qty, precision_rounding=rounding
            )
            >= 0
        ):
            availability_status = "full"
            available_qty = self.product_uom_qty
        # Partially available
        elif float_compare(available_qty, 0, precision_rounding=rounding) == 1:
            availability_status = "partial"
        # No stock
        elif float_is_zero(available_qty, precision_rounding=rounding):
            product_replenishment_date = product._get_next_replenishment_date()
            # Replenishment ordered
            if product_replenishment_date:
                availability_status = "restock"
                expected_availability_date = product_replenishment_date
        return {
            "availability_status": availability_status,
            "expected_availability_date": expected_availability_date,
            "available_qty": available_qty,
        }
