# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    in_geo_release_channel = fields.Boolean(
        string="Delivery based on geo-localization?",
        help="Include in release channels based on geographic zones",
        default=True,
    )
    located_in_stock_release_channel_ids = fields.Many2many(
        comodel_name="stock.release.channel",
        string="Located in",
        compute="_compute_located_in_stock_release_channel_ids",
        help="This partner is located within those release channels.",
    )

    @api.depends("geo_point", "in_geo_release_channel")
    def _compute_located_in_stock_release_channel_ids(self):
        for rec in self:
            if not rec.geo_point or not rec.in_geo_release_channel:
                rec.located_in_stock_release_channel_ids = False
                continue
            rec.located_in_stock_release_channel_ids = (
                rec.located_in_stock_release_channel_ids.search(
                    [("delivery_zone", "geo_intersect", rec.geo_point)]
                )
            )
