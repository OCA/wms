# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo.tools import sql

_logger = logging.getLogger(__name__)


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
