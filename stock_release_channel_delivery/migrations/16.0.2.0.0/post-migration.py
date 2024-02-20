# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):

    openupgrade.m2o_to_x2m(
        env.cr,
        env["stock.release.channel"],
        "stock_release_channel",
        "carrier_ids",
        openupgrade.get_legacy_name("carrier_id"),
    )
