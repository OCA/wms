# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockDeviceTypeLine(models.Model):

    _name = "stock.device.type.line"
    _description = "Stock Device Type Line"

    name = fields.Char()
    stock_device_type_id = fields.Many2one(
        "stock.device.type", string="Stock Device Type", required=True,
    )
    sequence = fields.Integer(string="Priority")
