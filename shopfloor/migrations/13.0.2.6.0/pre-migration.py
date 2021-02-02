# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from openupgradelib import openupgrade  # pylint: disable=W7936


@openupgrade.migrate()
def migrate(env, version):
    if not version:
        return
    openupgrade.copy_columns(
        env.cr,
        {
            "res_partner": [
                ("shopfloor_packing_info", "shopfloor_packing_info_tmp", None,)
            ],
        },
    )
