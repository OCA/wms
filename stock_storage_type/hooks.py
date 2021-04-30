# -*- coding: utf-8 -*-
# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def column_exists(cr, tablename, columnname):
    """ Return whether the given column exists. """
    query = """ SELECT 1 FROM information_schema.columns
                WHERE table_name=%s AND column_name=%s """
    cr.execute(query, (tablename, columnname))
    return cr.rowcount


def add_pack_operation_state_column(cr):
    _logger.info("Add column state on pack_operation")

    if not column_exists(cr, "stock_pack_operation", "state"):
        cr.execute(
            """
            ALTER TABLE stock_pack_operation
            ADD COLUMN state varchar;
        """
        )
        cr.execute(
            """
            UPDATE stock_pack_operation
            SET state = p.state
            FROM stock_picking p
            WHERE p.id = stock_pack_operation.picking_id
        """
        )


def pre_init_hook(cr):
    add_pack_operation_state_column(cr)
