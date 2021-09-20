# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockDeviceType(models.Model):

    _name = "stock.device.type"
    _description = "Stock Device Type"

    name = fields.Char()
    min_volume = fields.Float(
        string="Minimum total net volume for electing this device (in m3)"
    )
    max_volume = fields.Float(
        string="Maximum total net volume for electing this device (in m3)"
    )
    max_weight = fields.Float(
        string="Maximum total net weight for electing this device (in kg)"
    )
    nbr_bins = fields.Integer(string="Number of compartments")

    stock_device_type_line_ids = fields.One2many(
        comodel_name="stock.device.type.line",
        inverse_name="stock_device_type_id",
        string="Informations about stock device type",
    )