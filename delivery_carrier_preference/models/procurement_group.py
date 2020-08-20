# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    picking_ids = fields.One2many(
        comodel_name="stock.picking", inverse_name="group_id", readonly=True
    )
