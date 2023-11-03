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
    checkout_scenario = env["shopfloor.scenario"].search([("key", "=", "checkout")])
    _update_scenario_options(checkout_scenario)
    checkout_menus = env["shopfloor.menu"].search(
        [("scenario_id", "=", checkout_scenario.id)]
    )
    _enable_option_in_menus(checkout_menus)


def _update_scenario_options(scenario):
    options = scenario.options
    options["ask_for_leaf_destination_location"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option ask_for_leaf_destination_location added to the Checkout scenario"
    )


def _enable_option_in_menus(menus):
    for menu in menus:
        menu.ask_for_leaf_destination_location = True
        _logger.info(
            "Option ask_for_leaf_destination_location enabled for menu {}".format(
                menu.name
            )
        )
