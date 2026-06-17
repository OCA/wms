import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    location_content_transfer = env.ref("shopfloor.scenario_location_content_transfer")
    _update_scenario_options(location_content_transfer)


def _update_scenario_options(scenario):
    options = scenario.options
    options["allow_quantity_exceeding_demand"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option 'allow_quantity_exceeding_demand' added to scenario %s",
        scenario.name,
    )
