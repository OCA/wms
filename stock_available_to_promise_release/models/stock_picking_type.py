# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import fields, models


class StockPickingType(models.Model):
    _inherit = "stock.picking.type"

    count_picking_need_release = fields.Integer(compute="_compute_picking_count")

    def _compute_picking_count_need_release_domains(self):
        return {
            "count_picking_waiting": [
                ("state", "in", ("confirmed", "waiting")),
                ("need_release", "=", False),
            ],
            "count_picking_late": [
                ("scheduled_date", "<", fields.Datetime.now()),
                ("state", "in", ("assigned", "waiting", "confirmed")),
                ("need_release", "=", False),
            ],
            "count_picking_need_release": [("need_release", "=", True)],
        }

    def _compute_picking_count(self):
        super()._compute_picking_count()
        # hopefully refactor with https://github.com/odoo/odoo/pull/61696
        # currently, we have to compute twice "count_picking_late" and
        # "count_picking_waiting", to remove the "need_release" records
        domains = self._compute_picking_count_need_release_domains()
        for field, domain in domains.items():
            data = self.env["stock.picking"].read_group(
                domain
                + [
                    ("state", "not in", ("done", "cancel")),
                    ("picking_type_id", "in", self.ids),
                ],
                ["picking_type_id"],
                ["picking_type_id"],
            )
            count = {
                row["picking_type_id"][0]: row["picking_type_id_count"]
                for row in data
                if row["picking_type_id"]
            }
            for record in self:
                record[field] = count.get(record.id, 0)

        for record in self:
            if record.count_picking:
                # as we modify the 'late' stat, update the rate
                record.rate_picking_late = (
                    record.count_picking_late * 100 / record.count_picking
                )

    def get_action_picking_tree_need_release(self):
        xmlid = "stock_available_to_promise_release.stock_picking_release_action"
        return self._get_action(xmlid)
