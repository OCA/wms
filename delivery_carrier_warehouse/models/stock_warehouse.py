# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    delivery_carrier_id = fields.Many2one(
        "delivery.carrier",
        string="Delivery Method",
        help="Default delivery method used in sales orders. Will be applied "
        "only if the partner does not have a default delivery method.",
    )
