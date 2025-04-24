import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    reception = env.ref("shopfloor_reception.scenario_reception")
    _update_scenario_options(
        reception, sort_order=False, additional_domain=True, today=True
    )


def _update_scenario_options(
    scenario, sort_order=True, additional_domain=True, today=True
):
    options = scenario.options
    options["allow_move_line_search_sort_order"] = sort_order
    options["allow_move_line_search_additional_domain"] = additional_domain
    options["allow_filter_today_scheduled_pickings"] = today
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option allow_move_line_search_additional_domain added to scenario %s",
        scenario.name,
    )
