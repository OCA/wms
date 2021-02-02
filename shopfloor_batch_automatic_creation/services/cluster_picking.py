# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    def _select_a_picking_batch(self, batches):
        batch = super()._select_a_picking_batch(batches)
        if not batch and self.work.menu.batch_create:
            batch = self._batch_auto_create()
            batch.write({"user_id": self.env.uid, "state": "in_progress"})
        return batch

    def _batch_auto_create(self):
        auto_batch = self._actions_for("picking.batch.auto.create")
        menu = self.work.menu
        return auto_batch.create_batch(
            self.picking_types,
            group_by_commercial_partner=menu.batch_group_by_commercial_partner,
            max_pickings=menu.batch_create_max_picking,
            max_volume=menu.batch_create_max_volume,
            max_weight=menu.batch_create_max_weight,
        )
