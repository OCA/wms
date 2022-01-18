# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.tools import float_compare


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def _action_done(self):
        # In std Odoo we are not supposed to split & validate moves
        # independently in only one receipt, and Odoo assumes that there is
        # only one move corresponding to a MO, so if we receive more qty than
        # the expected one, Odoo will automatically update the MO produced qty
        # with the quantity done of the move.
        # But with the reception screen, as several moves could be created from
        # the original one, we need to update this produced qty by grouping all
        # moves sharing the same MO.
        # Here we disable some std behavior with the 'subcontracting_skip_action_done'
        # context key and we rewrite the business logic.
        new_self = self
        if any(picking._is_subcontract() for picking in self):
            new_self = self.with_context(subcontracting_skip_action_done=True)
        res = super(StockPicking, new_self)._action_done()
        for picking in self.filtered(lambda p: p._is_subcontract()):
            productions = picking.move_lines.move_orig_ids.production_id.filtered(
                lambda p: p.state not in ("done", "cancel")
            )[-1:]
            for production in productions:
                # Update the qty to produce as it is done in 'mrp_subcontracting'
                # but we group all received moves sharing the same MO here.
                moves = production.move_finished_ids.move_dest_ids.filtered(
                    lambda m: (
                        m.picking_id == picking
                        and not m._has_tracked_subcontract_components()
                    )
                )
                if not moves:
                    continue
                quantity_done = sum(
                    move.product_uom._compute_quantity(
                        move.quantity_done, production.product_uom_id
                    )
                    for move in moves
                )
                received_more_qty = (
                    float_compare(
                        production.product_qty,
                        quantity_done,
                        precision_rounding=production.product_uom_id.rounding,
                    )
                    == -1
                )
                if received_more_qty:
                    change_qty = self.env["change.production.qty"].create(
                        {"mo_id": production.id, "product_qty": quantity_done}
                    )
                    change_qty.with_context(skip_activity=True).change_prod_qty()
                production.qty_producing = quantity_done
                production._set_qty_producing()

            # Validate MO as it is done in 'mrp_subcontracting'
            productions_to_done = (
                picking._get_subcontracted_productions()._subcontracting_filter_to_done()
            )
            production_ids_backorder = []
            if not self.env.context.get("cancel_backorder"):
                production_ids_backorder = productions_to_done.filtered(
                    lambda mo: mo.state == "progress"
                ).ids
            productions_to_done.with_context(
                subcontract_move_id=True, mo_ids_to_backorder=production_ids_backorder
            ).button_mark_done()
        return res
