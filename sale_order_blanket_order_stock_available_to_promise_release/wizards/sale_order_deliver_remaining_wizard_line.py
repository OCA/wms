# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrderDeliverRemainingWizardLine(models.TransientModel):
    _inherit = "sale.order.deliver.remaining.wizard.line"

    availability_status = fields.Selection(
        related="sale_order_line_id.availability_status",
        readonly=True,
    )
    expected_availability_date = fields.Datetime(
        related="sale_order_line_id.expected_availability_date",
        readonly=True,
    )
    available_qty = fields.Float(
        related="sale_order_line_id.available_qty",
        readonly=True,
        digits="Product Unit of Measure",
    )
    delayed_qty = fields.Float(
        string="Missing Quantity",
        related="sale_order_line_id.delayed_qty",
        readonly=True,
        digits="Product Unit of Measure",
    )
