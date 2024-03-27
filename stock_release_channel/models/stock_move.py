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
        res = super().release_available_to_promise()
        # As moves can be merged (and then unlinked), we should ensure
        # they still exist.
        moves = self.exists()
        company = self.env.company
        if company.recompute_channel_on_pickings_at_release:
            moves.picking_id.assign_release_channel()
        return res

    def _action_confirm(self, merge=True, merge_into=False):
        moves = super()._action_confirm(merge=merge, merge_into=merge_into)
        pickings = moves.filtered("need_release").picking_id
        if pickings:
            pickings._delay_assign_release_channel()
        return moves

    def _release_get_expected_date(self):
        """Return the new scheduled date of a single delivery move"""
        channel = self.picking_id.release_channel_id
        expected_date = channel and channel._get_expected_date()
        if not expected_date:
            return super()._release_get_expected_date()
        return expected_date
