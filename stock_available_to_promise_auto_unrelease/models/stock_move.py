# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from contextlib import contextmanager

from odoo import _, models
from odoo.tools import float_compare


class StockMove(models.Model):

    _inherit = "stock.move"

    def _recompute_state(self):
        """Recompute the state of the stock move."""
        # This method is overridden to ensure that the state is recomputed
        # correctly after the free reservation process.
        with self._unrelease_moves():
            return super()._recompute_state()

    def _should_be_auto_unreleased(self):
        """Check if the move is unreleasable."""
        self.ensure_one()
        return (
            self.state in ["assigned", "partially_available"]
            and self.picking_type_id.unrelease_on_unavailable_to_promise
        )

    @contextmanager
    def _unrelease_moves(self):
        """Context manager to handle moves that need to be unreleased.

        This method is used to unrelease moves due to state changes from 'assigned'
        or 'partially_available' to 'confirmed'.
        """
        observed_moves = self.filtered(lambda move: move._should_be_auto_unreleased())
        # This method can be used to manage moves that need to be unreleased
        # after the free reservation process.
        yield self
        unreserved_moves = observed_moves.filtered(
            lambda move: move.state == "confirmed"
        )
        sudo_moves_to_unrelease = (
            unreserved_moves.sudo()._get_origin_move_to_unrelease()
        )
        sudo_moves_to_unrelease._delay_unrelease()

    def _get_origin_move_to_unrelease(self):
        """Get the first move that was released and needs to be unreleased.

        This method iterates through the chained moves to find those that
        are released and could be unreleased
        """
        to_unrelease = self.browse()
        for move in self:
            iterator = move._get_chained_moves_iterator("move_dest_ids")
            next(iterator)
            for moves_dest in iterator:
                match = moves_dest.filtered(
                    lambda m: m.picking_type_id.code == "outgoing"
                    and m.unrelease_allowed
                )
                if match:
                    to_unrelease |= match
                    break
        return to_unrelease

    def _delay_unrelease(self):
        for move in self:
            description = _(
                "Unrelease move %(product_names)s from picking %(picking_name)s"
            ) % {
                "product_names": ", ".join(move.product_id.mapped("name")),
                "picking_name": move.picking_id.name,
            }
            move.with_delay(
                description=description,
            )._do_unrelease_no_more_available()

    def _do_unrelease_no_more_available(self):
        """Safely unrelease the moves that were delayed."""
        # we ensure that the ordered_available_to_promise_qty is up to date
        # and will be computed only for the moves candidates to unrelease
        to_unrelease = self.browse()
        to_unrelease_candidates = self.exists()
        # We only take into account the criteria on the ordered_available_to_promise_qty
        # at this stage since when it's not yet relevant when the state of a move changes
        # due to a free reservation. Indeed, the move is updated before the quant is updated
        # since this method is delayed, at this point, the quant is already updated
        to_unrelease_candidates.invalidate_recordset(
            ["ordered_available_to_promise_qty"]
        )
        to_unrelease_candidates = to_unrelease_candidates.with_prefetch(
            to_unrelease_candidates.ids
        )
        for move in to_unrelease_candidates:
            rounding = self.product_id.uom_id.rounding
            if (
                float_compare(
                    move.ordered_available_to_promise_qty,
                    0,
                    precision_rounding=rounding,
                )
                <= 0
            ):
                to_unrelease |= move
        return to_unrelease.unrelease(safe_unrelease=True)
