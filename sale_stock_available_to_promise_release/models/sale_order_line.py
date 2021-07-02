# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models
from odoo.tools import float_compare, float_is_zero


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    availability_status = fields.Selection(
        selection=[
            ("mto", "On order"),
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

    @api.depends(
        "move_ids.ordered_available_to_promise_uom_qty",
        "product_id.route_ids",
        "product_uom_qty",
    )
    def _compute_availability_status(self):
        for record in self:
            # Fallback values
            availability_status = "no"
            expected_availability_date = False
            available_qty = sum(
                record.mapped("move_ids.ordered_available_to_promise_uom_qty")
            )
            # required values
            product = record.product_id
            rounding = product.uom_id.rounding
            mto_route = self.env.ref("stock.route_warehouse0_mto")
            # MTO product
            if mto_route in product.route_ids:
                availability_status = "mto"
            # Fully available
            elif (
                float_compare(
                    available_qty, record.product_uom_qty, precision_rounding=rounding
                )
                >= 0
            ):
                availability_status = "full"
                available_qty = record.product_uom_qty
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
            record.availability_status = availability_status
            record.expected_availability_date = expected_availability_date
            record.available_qty = available_qty
