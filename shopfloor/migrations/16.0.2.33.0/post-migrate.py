import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    scenario_xml_ids = [
        "shopfloor.scenario_location_content_transfer",
        "shopfloor.scenario_zone_picking",
        "shopfloor.scenario_cluster_picking",
    ]
    for scenario_xml_id in scenario_xml_ids:
        scenario = env.ref(scenario_xml_id)
        _update_scenario_options(scenario)


def _update_scenario_options(scenario):
    options = scenario.options
    options["uses_stock_issue"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option 'uses_stock_issue' added to scenario %s",
        scenario.name,
    )
