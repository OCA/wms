# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Updating scenario Zone Picking")
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    zone_picking_scenario = env.ref("shopfloor.scenario_zone_picking")
    _update_scenario_options(zone_picking_scenario)


def _update_scenario_options(scenario):
    options = scenario.options
    if "require_destination_package" not in options:
        options["require_destination_package"] = True
        options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
        scenario.write({"options_edit": options_edit})
        _logger.info(
            "Option require_destination_package added to scenario Zone Picking"
        )
