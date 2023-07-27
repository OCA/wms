# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import models


class StockMove(models.Model):

    _inherit = "stock.move"

    def _after_release_update_chain(self):
        self._propagate_release_channel()
        return super()._after_release_update_chain()

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
            moves = move.mapped("move_orig_ids")
            while moves:
                pickings_per_channel[move.picking_id.release_channel_id].update(
                    moves.picking_id.ids
                )
                moves = moves.mapped("move_orig_ids")
        for channel, picking_ids in pickings_per_channel.items():
            pickings = self.env["stock.picking"].browse(picking_ids)
            pickings_updated |= pickings
            pickings.write({"release_channel_id": channel.id})
        return pickings_updated
