# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    propagate_to_pickings_chain = fields.Boolean(
        help="Check this field if you want to propagate the channel from the"
        "outgoing pickings to the internal ones."
    )
