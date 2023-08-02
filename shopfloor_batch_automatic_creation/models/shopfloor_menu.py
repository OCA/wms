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
    batch_maximum_number_of_preparation_lines = fields.Integer(
        default=20,
        string="Maximum number of preparation lines for the batch",
        required=True,
    )
    stock_device_type_ids = fields.Many2many(
        comodel_name="stock.device.type",
        relation="shopfloor_menu_device_type_rel",
        column1="shopfloor_menu_id",
        column2="device_type_id",
        string="Default device types",
        help="Default list of eligible device types when creating a batch transfer",
    )
