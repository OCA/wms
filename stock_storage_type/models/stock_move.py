# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import api, models


class StockMove(models.Model):

    _inherit = "stock.move"

    @api.model
    def create(self, vals):
        res = super(StockMove, self).create(vals)
        res.location_dest_id.invalidate_cache(["in_move_ids"], res.location_dest_id.ids)
        res.location_dest_id._tigger_cache_recompute_if_required()
        return res

    def write(self, vals):
        location_dest_ids = []
        if "location_dest_id" in vals:
            location_dest_ids.extend(self.mapped("location_dest_id").ids)
        res = super(StockMove, self).write(vals)
        location_dest_ids.extend(self.mapped("location_dest_id").ids)
        locations = self.env["stock.location"].browse(location_dest_ids)
        if "state" in vals:
            locations.invalidate_cache(["in_move_ids"], locations.ids)
        locations._tigger_cache_recompute_if_required()
        return res

    def unlink(self):
        locations = self.mapped("location_dest_id")
        res = super(StockMove, self).unlink()
        locations.invalidate_cache(["in_move_ids"], locations.ids)
        locations._tigger_cache_recompute_if_required()
        return res
