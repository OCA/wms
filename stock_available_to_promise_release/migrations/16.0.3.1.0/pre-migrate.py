# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    """
    Initialize default value when adding field instead updating every record.
    """

    field_spec = [
        (
            "release_policy",
            "stock.picking",
            False,
            "char",
            "varchar",
            "stock_available_to_promise_release",
            "direct",
        )
    ]

    openupgrade.add_fields(env, field_spec=field_spec)
