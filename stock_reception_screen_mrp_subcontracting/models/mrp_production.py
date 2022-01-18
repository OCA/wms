# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


class MrpProduction(models.Model):
    _inherit = "mrp.production"

    def _set_qty_producing(self):
        # Inhibited during the call of 'stock.picking._action_done()' of
        # 'mrp_subcontracting' addon.
        if self.env.context.get("subcontracting_skip_action_done"):
            return False
        return super()._set_qty_producing()

    def button_mark_done(self):
        # Inhibited during the call of 'stock.picking._action_done()' of
        # 'mrp_subcontracting' addon.
        if self.env.context.get("subcontracting_skip_action_done"):
            return False
        return super().button_mark_done()
