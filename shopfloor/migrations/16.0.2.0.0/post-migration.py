# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    zone_picking_scenario = env["shopfloor.scenario"].search(
        [("name", "=", "Zone Picking")]
    )
    _update_scenario_options(zone_picking_scenario)
    zone_picking_menus = env["shopfloor.menu"].search(
        [("scenario_id", "=", zone_picking_scenario.id)]
    )
    _enable_option_in_menus(zone_picking_menus)


def _update_scenario_options(scenario):
    options = scenario.options
    options["allow_alternative_destination_package"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option allow_alternative_destination_package added to scenario Zone Picking"
    )


def _enable_option_in_menus(menus):
    for menu in menus:
        menu.allow_alternative_destination_package = True
        _logger.info(
            "Option allow_alternative_destination_package enabled for menu {}".format(
                menu.name
            )
        )
