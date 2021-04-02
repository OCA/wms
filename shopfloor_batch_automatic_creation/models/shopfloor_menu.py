# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    batch_create = fields.Boolean(
        string="Automatic Batch Creation",
        default=False,
        help='Automatically create a batch when an operator uses the "Get Work"'
        " button and no existing batch has been found. The system will first look"
        " for priority transfers and fill up the batch till the defined"
        " constraints (max of transfers, volume, weight, ...)."
        " It never mixes priorities, so if you get 2 available priority transfers"
        " and a max quantity of 3, the batch will only contain the 2"
        " priority transfers.",
    )
    batch_group_by_commercial_partner = fields.Boolean(
        string="Group by commercial entity",
        default=False,
        help="If enabled, transfers will be grouped by commercial entity."
        "This could mix priorities and will ignore the constraints to apply.",
    )
    batch_create_max_picking = fields.Integer(
        string="Max transfers",
        default=0,
        help="Maximum number of transfers to add in an automatic batch."
        " 0 means no limit.",
    )
    batch_create_max_volume = fields.Float(
        string="Max volume (m³)",
        default=0,
        digits=(8, 4),
        help="Maximum volume in cubic meters of goods in transfers to"
        " add in an automatic batch. 0 means no limit.",
    )
    batch_create_max_weight = fields.Float(
        string="Max Weight (kg)",
        default=0,
        help="Maximum weight in kg of goods in transfers to add"
        " in an automatic batch. 0 means no limit.",
    )
