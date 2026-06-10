# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """
        ALTER TABLE stock_route
        ADD COLUMN IF NOT EXISTS
            autoblock_release_on_backorder_legacy boolean
        """
    )

    cr.execute(
        """
        UPDATE stock_route
           SET autoblock_release_on_backorder_legacy =
               autoblock_release_on_backorder
        """
    )
