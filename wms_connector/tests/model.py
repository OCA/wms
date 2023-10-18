# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models

import uuid


class WmsProductSync(models.Model):
    _inherit = ["wms.product.sync"]

    def _prepare_export_data(self):
        res = []
        for rec in self:
            res += [
                {"name": rec.product_id.name, "reference": rec.product_id.default_code}
            ]
            if len(rec.product_id.name) > 100:
                raise ValueError("Boom")
        return res

    def _get_export_name(self):
        return self.name


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _prepare_export_data(self):
        return [
            {
                "name": rec.name,
            }
            for rec in self
        ]

    def _get_export_name(self):
        return self.name
