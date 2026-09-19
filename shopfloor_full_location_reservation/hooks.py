# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from odoo import SUPERUSER_ID, api


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})

    for scenario in [
        env.ref("shopfloor.scenario_location_content_transfer"),
        env.ref("shopfloor.scenario_zone_picking"),
    ]:
        options = scenario.options
        options["full_location_reservation"] = True
        scenario.options_edit = json.dumps(options)
