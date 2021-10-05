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
    total_weight_batch_picking = fields.Float(string= "Weight",help="Indicates total weight of transfers included.")
    total_volume_batch_picking = fields.Float(string= "Volume",help="Indicates total volume of transfers included.")
    nbr_bins_batch_picking = fields.Integer(string= "Number of compartments", help="Indicates the bins occupied by the picking on the device.")
    nbr_picking_lines = fields.Integer(string= "Number of lines", help="Indicates the picking lines ready for preparation.")