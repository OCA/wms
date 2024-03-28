# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        ondelete="set null",
        string="Force Release Channel",
        help=(
            "Force the release channel on deliveries. "
            "This will ignore customer preferences."
        ),
        domain=(
            "warehouse_id and "
            "['|', ('warehouse_id', '=', warehouse_id), ('warehouse_id', '=', False)] "
            "or []"
        ),
    )
