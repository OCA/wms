# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def _check_overprocessed_subcontract_qty(self):
        # Disable the check if finished move lines have been removed by the
        # `_action_done_picking` method of the reception screen (resetting the
        # 'qty_produced' computed field of the production order to 0). Indeed,
        # these move lines are automatically recreated by the 'mrp_subcontracting'
        # module in the picking 'action_done()' override by duplicating received
        # move lines, so the production order will get its 'qty_produced' correct
        # afterwards anyway.
        # We know that we come from a validation of the reception screen thanks
        # to the 'subcontracting_skip_unlink' context key defined in
        # '_action_done_picking' method of the reception screen.
        if self.env.context.get("subcontracting_skip_unlink"):
            return False
        return super()._check_overprocessed_subcontract_qty()
