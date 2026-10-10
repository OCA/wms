# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    scenario = env.ref(
        "shopfloor_single_product_transfer.scenario_single_product_transfer"
    )
    options = scenario.options
    options["full_location_reservation"] = True
    scenario.options_edit = json.dumps(options)
