# Copyright 2023 Akretion
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.addons.wms_connector.pydantic_models.stock_picking import StockPickingExporter


class StockPicking(models.Model):
    _inherit = ["stock.picking", "synchronize.exportable.mixin"]

    def _prepare_export_data(self):
        return StockPickingExporter.from_orm(self)
