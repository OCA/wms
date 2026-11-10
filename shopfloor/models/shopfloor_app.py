# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ShopfloorApp(models.Model):
    _inherit = "shopfloor.app"

    category = fields.Selection(selection_add=[("wms", "WMS")])
    show_counters = fields.Boolean(
        default=True,
        help="If checked, display move line counters on menu items.",
    )
