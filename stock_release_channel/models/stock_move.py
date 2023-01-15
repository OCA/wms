# Copyright 2020 Camptocamp
# Copyright 2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def release_available_to_promise(self):
        # after releasing, we re-assign a release channel,
        # as we may release only partially, the channel may
        # change
        released_moves = super().release_available_to_promise()
        released_moves.picking_id.assign_release_channel()
        return released_moves

    def _assign_picking(self):
        res = super()._assign_picking()
        pickings = self.filtered("need_release").picking_id
        if pickings:
            pickings._delay_assign_release_channel()
        return res
