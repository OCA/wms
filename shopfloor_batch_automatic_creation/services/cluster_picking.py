# Copyright 2020 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tools.safe_eval import safe_eval

from odoo.addons.component.core import Component


class ClusterPicking(Component):
    _inherit = "shopfloor.cluster.picking"

    def _select_a_picking_batch(self, batches):
        batch = super()._select_a_picking_batch(batches)
        if not batch and self.work.menu.batch_create:
            batch = self._batch_auto_create()
        if batch:
            batch.action_confirm()
        return batch

    def _batch_auto_create(self):
        auto_batch = self._actions_for("picking.batch.auto.create")
        menu = self.work.menu
        return auto_batch.create_batch(
            self.picking_types,
            group_by_commercial_partner=menu.batch_group_by_commercial_partner,
            maximum_number_of_preparation_lines=menu.batch_maximum_number_of_preparation_lines,
            stock_device_types=menu.stock_device_type_ids,
            shopfloor_menu=menu,
        )

    def _sort_key_lines(self, line):
        # we get the device from the batch
        device = line.batch_id.picking_device_id
        # the sort key code is protected by the group base.group_system
        sudo_device = device.sudo()
        code = sudo_device.line_sort_key_code and sudo_device.line_sort_key_code.strip()
        if code:
            context = {
                "line": line,
                "super": super()._sort_key_lines,
                "key": None,
            }
            safe_eval(code, context, mode="exec", nocopy=True)
            return context["key"]
        return super()._sort_key_lines(line)
