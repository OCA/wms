# Copyright 2021 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("Linking existing menu items to their scenario")
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Ensure scenario are linked to menu items
    env["shopfloor.menu"].with_context(active_test=False).search(
        [("scenario_id", "=", False)]
    )._compute_scenario_id()
