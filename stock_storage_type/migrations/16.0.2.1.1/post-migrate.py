# Copyright 2026 ACSONE SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):

    _logger.info("Initializing potential mix exception columns on stock_location")
    cr.execute(
        """
        UPDATE stock_location
        SET
            has_potential_lot_mix_exception     = (
                fill_state NOT IN ('empty', 'being_emptied') IS TRUE
                AND COALESCE(counts.lot_cnt, 0) > 1
            ),
            has_potential_product_mix_exception = (
                fill_state NOT IN ('empty', 'being_emptied') IS TRUE
                AND COALESCE(counts.product_cnt, 0) > 1
            )
        FROM (
            SELECT
                sl.id,
                COUNT(DISTINCT lrel.stock_lot_id)         AS lot_cnt,
                COUNT(DISTINCT prel.product_product_id)   AS product_cnt
            FROM stock_location sl
            LEFT JOIN stock_location_stock_lot_rel lrel
                ON lrel.stock_location_id = sl.id
            LEFT JOIN product_product_stock_location_rel prel
                ON prel.stock_location_id = sl.id
            GROUP BY sl.id
        ) AS counts
        WHERE stock_location.id = counts.id;
            """
    )
    _logger.info("Potential mix exception columns on stock_location initialized")
    _logger.info("%d stock_location records updated", cr.rowcount)
