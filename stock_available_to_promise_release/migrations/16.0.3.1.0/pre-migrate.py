# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from openupgradelib import openupgrade

# pylint: disable=odoo-addons-relative-import
from odoo.addons.stock_available_to_promise_release.hooks import init_release_policy


@openupgrade.migrate()
def migrate(env, version):
    """
    Use the default sql query instead relying on ORM as all records will
    be updated.
    """
    init_release_policy(env.cr)
