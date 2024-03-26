# Copyright 2024 Akretion (https://www.akretion.com).
# @author Sébastien BEAU <sebastien.beau@akretion.com>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def create(self, list_vals):
        records = super().create(list_vals)
        records.picking_id._wms_check_if_editable()
        return records

    def _wms_protected_fields(self):
        return ["picking_id", "product_id", "product_qty"]

    def write(self, vals):
        if set(vals).intersection(self._wms_protected_fields()):
            pickings = (
                self.env["stock.picking"].browse(vals.get("picking_id"))
                | self.picking_id
            )
            pickings._wms_check_if_editable()
        return super().write(vals)

    def unlink(self):
        self.picking_id._wms_check_if_editable()
        return super().unlink()

    def _action_done(self, cancel_backorder=False):
        return super(
            StockMove, self.with_context(skip_check_protected_fields=True)
        )._action_done(cancel_backorder=cancel_backorder)
