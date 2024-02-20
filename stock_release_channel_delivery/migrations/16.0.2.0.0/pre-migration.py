# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "stock_release_channel", "carrier_id"):
        openupgrade.rename_columns(
            env.cr, {"stock_release_channel": [("carrier_id", None)]}
        )
