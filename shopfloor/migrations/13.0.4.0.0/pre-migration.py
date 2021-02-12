# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools import column_exists, table_exists


def migrate(cr, version):
    # Scenario reference changed on split to shopfloor_base
    if column_exists(cr, "shopfloor_menu", "scenario") and table_exists(
        cr, "shopfloor_scenario"
    ):
        cr.execute(
            """
            UPDATE
                shopfloor_menu
            SET
                scenario_id = shopfloor_scenario.id
            FROM
                shopfloor_scenario
            WHERE
                shopfloor_menu.scenario = shopfloor_scenario.key
            """
        )
