# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models


class SaleOrderDeliverRemainingWizard(models.TransientModel):
    _inherit = "sale.order.deliver.remaining.wizard"

    availability_filter = fields.Selection(
        selection=lambda self: [("all", _("All remaining lines"))]
        + self.env["sale.order.line"]
        ._fields["availability_status"]
        ._description_selection(self.env),
        default="all",
        required=True,
    )

    @api.onchange("availability_filter")
    def _onchange_availability_filter(self):
        """show remaining lines matching the selected availability status"""
        lines = self.order_id.order_line
        self.wizard_line_ids = [Command.clear()] + [
            Command.create(
                {
                    "sale_order_line_id": line.id,
                    "qty_to_deliver": line.call_off_remaining_qty,
                }
            )
            for line in lines
            if line.call_off_remaining_qty > 0
            and (
                self.availability_filter == "all"
                or line.availability_status == self.availability_filter
            )
        ]
