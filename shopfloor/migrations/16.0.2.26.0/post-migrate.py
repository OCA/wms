import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    cluster_picking_scenario = env.ref("shopfloor.scenario_cluster_picking")
    _update_scenario_options(cluster_picking_scenario)


def _update_scenario_options(scenario):
    options = scenario.options
    options["force_detailed_scan"] = True
    options_edit = json.dumps(options or {}, indent=4, sort_keys=True)
    scenario.write({"options_edit": options_edit})
    _logger.info(
        "Option 'force_detailed_scan' added to scenario %s",
        scenario.name,
    )
