# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    stock_release_channel_ids = fields.Many2many(
        comodel_name="stock.release.channel",
        relation="res_partner_stock_release_channel_rel",
        column1="partner_id",
        column2="channel_id",
        string="Release Channels",
        domain="company_id and [('company_id', '=', company_id)] or []",
    )
