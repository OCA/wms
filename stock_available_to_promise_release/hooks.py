# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import logging

from openupgradelib import openupgrade

from odoo import SUPERUSER_ID, api
from odoo.tools import sql

_logger = logging.getLogger(__name__)


def init_release_policy(cr):
    if not sql.column_exists(cr, "stock_picking", "release_policy"):
        # Use the default sql query instead relying on ORM as all records will
        # be updated.
        _logger.info("Creating 'release_policy' field on stock.picking")
        env = api.Environment(cr, SUPERUSER_ID, {})
        field_spec = [
            (
                "release_policy",
                "stock.picking",
                False,
                "selection",
                False,
                "stock_available_to_promise_release",
                "direct",
            )
        ]
        openupgrade.add_fields(env, field_spec=field_spec)


def pre_init_hook(cr):
    """create and initialize the date priority column on the stock move"""
    if not sql.column_exists(cr, "stock_move", "date_priority"):
        _logger.info("Create date_priority column")
        cr.execute(
            """
            ALTER TABLE stock_move
            ADD COLUMN date_priority timestamp;
        """
        )
        _logger.info("Initialize date_priority field")
        cr.execute(
            """
            UPDATE stock_move
            SET date_priority = create_date
            where state not in ('done', 'cancel')
        """
        )
        _logger.info(f"{cr.rowcount} rows updated")
    init_release_policy(cr)
