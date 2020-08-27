# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockLocationRoute(models.Model):

    _inherit = "stock.location.route"

    force_recompute_preferred_carrier_on_release = fields.Boolean(
        string="Force recomputation of preferred carrier.",
        help="Mark this box to trigger a recomputation of preferred carrier on"
        " the release of operations.",
    )
