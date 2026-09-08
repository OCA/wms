# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Updating scenario options for shopfloor_single_product_transfer")
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    single_product_transfer_scenario = env.ref(
        "shopfloor_single_product_transfer.scenario_single_product_transfer"
    )
    _update_scenario_options(single_product_transfer_scenario)


def _update_scenario_options(scenario):
    options = scenario.options
    if "allow_get_work" not in options:
        options["allow_get_work"] = True
        _logger.info("Option allow_get_work added to scenario %s", scenario.name)
    if "allow_move_line_search_sort_order" not in options:
        options["allow_move_line_search_sort_order"] = True
        options["allow_move_line_search_additional_domain"] = True
        _logger.info(
            "Option allow_alternative_destination_package added to scenario %s",
            scenario.name,
        )
    if "scan_location_or_pack_first" not in options:
        options["scan_location_or_pack_first"] = True
        _logger.info(
            "Option scan_location_or_pack_first added to scenario %s", scenario.name
        )
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
