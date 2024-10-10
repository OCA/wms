# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _after_release_update_chain(self):
        self._propagate_release_channel()
        return super()._after_release_update_chain()

    @property
    def move_origins_to_propagate_release_channel(self):
        """
        Get the origin moves for those release channel should be updated:

        - Don't take into account 'cancel' and 'done' moves
        - Don't take into account moves' picking that already have a release channel
        """
        return self.mapped("move_orig_ids").filtered(
            lambda m: m.state not in ("cancel", "done")
            and not m.picking_id.release_channel_id
        )

    def _propagate_release_channel(self):
        """
        We update the channel on corresponding pickings
        We update it per channel
        """
        pickings_per_channel = defaultdict(set)
        pickings_updated = self.env["stock.picking"]
        for move in self:
            if not move.picking_type_id.propagate_to_pickings_chain:
                continue
            moves = move.move_origins_to_propagate_release_channel
            while moves:
                pickings_per_channel[move.picking_id.release_channel_id].update(
                    moves.picking_id.ids
                )
                moves = moves.move_origins_to_propagate_release_channel
        for channel, picking_ids in pickings_per_channel.items():
            pickings = self.env["stock.picking"].browse(picking_ids)
            pickings_updated |= pickings
            pickings.write({"release_channel_id": channel.id})
        return pickings_updated
