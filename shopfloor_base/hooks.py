# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Ensure scenario are linked to menu items
    env["shopfloor.menu"].with_context(active_test=False).search(
        [("scenario_id", "=", False)]
    )._compute_scenario_id()
