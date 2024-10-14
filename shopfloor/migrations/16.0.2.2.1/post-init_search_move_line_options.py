# Copyright 2024 ACSONE SA/NV (http://acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    zone_picking = env.ref("shopfloor.scenario_zone_picking")
    _update_scenario_options(zone_picking, sort_order=False, additional_domain=True)
    location_content_transfer = env.ref("shopfloor.scenario_location_content_transfer")
    _update_scenario_options(
        location_content_transfer, sort_order=True, additional_domain=True
    )


def _update_scenario_options(scenario, sort_order=True, additional_domain=True):
    options = scenario.options
    options["allow_move_line_search_sort_order"] = sort_order
    options["allow_move_line_search_additional_domain"] = additional_domain
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option allow_alternative_destination_package added to scenario %s",
        scenario.name,
    )
