# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class StockInternalPackageConfigLine(models.Model):
    _name = "stock.internal.package.config.line"
    _description = "Internal Package Configuration Line"

    empty = fields.Boolean()
    delivery_carrier_id = fields.Many2one(
        "delivery.carrier",
        required=True,
        ondelete="cascade",
    )
    stock_picking_type_id = fields.Many2one(
        "stock.picking.type",
        required=True,
        readonly=True,
        ondelete="cascade",
    )

    def write(self, vals):
        res = super().write(vals)
        self._invalidate_empty_internal_package_on_transfer_cache()
        return res

    def _invalidate_empty_internal_package_on_transfer_cache(self):
        domain = [("stock_internal_package_config_line_ids", "in", self.ids)]
        picking_types = self.env["stock.picking.type"].search(domain)
        picking_types.clear_caches()
        self.env["stock.picking"].invalidate_model()
