# Copyright 2020 Camptocamp
# License OPL-1

from odoo import models


class StockMove(models.Model):
    _inherit = "stock.move"

    def release_available_to_promise(self):
        # after releasing, we re-assign a release channel,
        # as we may release only partially, the channel may
        # change
        super().release_available_to_promise()
        self.picking_id.assign_release_channel()
