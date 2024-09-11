# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    stock_release_channel_by_date_ids = fields.One2many(
        comodel_name="stock.release.channel.partner.date",
        inverse_name="partner_id",
        string="Additional Release Channels",
        help="Additional release channels for a specific delivery date.",
    )
