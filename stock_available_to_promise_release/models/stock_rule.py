# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockRule(models.Model):
    _inherit = "stock.rule"

    available_to_promise_defer_pull = fields.Boolean(
        related="route_id.available_to_promise_defer_pull", store=True
    )

    allow_unrelease_return_done_move = fields.Boolean(
        related="route_id.allow_unrelease_return_done_move", store=True
    )

    no_backorder_at_release = fields.Boolean(
        related="route_id.no_backorder_at_release", store=True
    )

    def _get_custom_move_fields(self):
        return super()._get_custom_move_fields() + ["date_priority"]

    def _run_pull(self, procurements):
        actions_to_run = []

        for procurement, rule in procurements:
            if (
                not self.env.context.get("_rule_no_available_defer")
                and rule.available_to_promise_defer_pull
                # We still want to create the first part of the chain
                # (outgoing for deliveries, incoming for inter-warehouse replenishment)
                and rule.picking_type_id.code == "internal"
            ):
                moves = procurement.values.get("move_dest_ids")
                # Mark downstream moves to be handled by deferred pull.
                # At this stage we only keep the first internal leg and do
                # not execute pull for the rest of the chain yet.
                # Setting need_release on destination moves prevents creating
                # next chained moves (pick/pack) until deferred pull runs.
                if moves:
                    moves.write({"need_release": True})
            else:
                actions_to_run.append((procurement, rule))

        super()._run_pull(actions_to_run)
        return True


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    def run_defer(self, procurements):
        actions_to_run = []
        for procurement in procurements:
            values = procurement.values
            values.setdefault("company_id", self.env.company)
            values.setdefault("priority", "1")
            values.setdefault("date_planned", fields.Datetime.now())
            rule = self._get_rule(
                procurement.product_id, procurement.location_id, procurement.values
            )
            if rule.action in ("pull", "pull_push"):
                actions_to_run.append((procurement, rule))

        if actions_to_run:
            rule.with_context(_rule_no_available_defer=True)._run_pull(actions_to_run)
        return True
