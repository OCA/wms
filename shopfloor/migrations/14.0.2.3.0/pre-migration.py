# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    queries = [
        """
            ALTER TABLE stock_move_line
            ADD COLUMN IF NOT EXISTS date_planned TIMESTAMP WITHOUT TIME ZONE
        """,
        """
            UPDATE stock_move_line
            SET date_planned=m.date
            FROM stock_move m
            WHERE move_id=m.id
            AND m.state NOT IN ('done', 'cancel');
        """,
    ]
    for query in queries:
        cr.execute(query)
