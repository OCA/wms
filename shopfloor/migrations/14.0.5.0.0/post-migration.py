# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import json

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    scenario = env.ref("shopfloor.scenario_cluster_picking")
    options = scenario.options
    options["allow_move_line_processing_sort_order"] = True
    scenario.write(
        {"options_edit": json.dumps(options or {}, indent=4, sort_keys=True)}
    )
