# Copyright 2024 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    reception_scenario = env["shopfloor.scenario"].search([("key", "=", "reception")])
    _update_scenario_options(reception_scenario)
    reception_menus = env["shopfloor.menu"].search(
        [("scenario_id", "=", reception_scenario.id)]
    )
    _enable_option_in_menus(reception_menus)


def _update_scenario_options(scenario):
    options = scenario.options
    options["display_vendor_packaging"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info("Option display_vendor_packaging added to scenario Reception")


def _enable_option_in_menus(menus):
    menus.display_vendor_packaging = True
    _logger.info("Option display_vendor_packaging enabled for reception menus")
