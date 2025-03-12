# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    outgoing_rules = env["stock.rule"].search(
        [("picking_type_id.code", "=", "outgoing")]
    )
    routes_to_update = env["stock.route"].search(
        [
            ("available_to_promise_defer_pull", "=", True),
            ("rule_ids", "in", outgoing_rules.ids),
        ]
    )
    _logger.info(f"disabling flow at confirm on {len(routes_to_update)} routes")
    routes_to_update.apply_flow_on = "on_release"
