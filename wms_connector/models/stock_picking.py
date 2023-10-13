# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models


class StockPicking(models.Model):
    _inherit = ["stock.picking", "synchronize.exportable.mixin"]
    _name = "stock.picking"

    def _get_export_name(self):
        if self.file_creation_mode == "per_record":
            return self.name + ".csv"
        return super()._get_export_name()
