# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShipmentAdvice(models.Model):
    _inherit = "shipment.advice"

    release_channel_id = fields.Many2one(
        comodel_name="stock.release.channel",
        string="Release Channel",
        states={"draft": [("readonly", False)]},
        readonly=True,
    )
