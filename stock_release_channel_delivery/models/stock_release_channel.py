# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    carrier_id = fields.Many2one(
        comodel_name="delivery.carrier",
        help="The carrier linked to the release channel.",
        string="Transporter",
    )
