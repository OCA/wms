# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def migrate(cr, version):
    cr.execute(
        """
        UPDATE stock_route
           SET autoblock_release_on_backorder =
               CASE
                   WHEN autoblock_release_on_backorder_legacy
                       THEN 'always'
                   ELSE 'never'
               END
        """
    )

    cr.execute(
        """
        ALTER TABLE stock_route
        DROP COLUMN IF EXISTS
            autoblock_release_on_backorder_legacy
        """
    )
