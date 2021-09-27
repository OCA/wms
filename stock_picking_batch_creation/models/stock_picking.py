# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"
    picking_device_id = fields.Many2one(
        "stock.device.type",
        string="Device for the picking",
        related="wave_id.picking_device_id",
        readonly=True,
    )

    user_id = fields.Many2one("res.users", string="Responsible", readonly=True)
    total_weight = fields.Float(help="Indicates total weight of transfers included.")
    total_volume = fields.Float(help="Indicates total volume of transfers included.")
    nbr_bins = fields.Float(help="Indicates the bins occupied by the picking on the device.")