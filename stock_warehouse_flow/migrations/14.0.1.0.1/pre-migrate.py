# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


def migrate(cr, installed_version):
    if not installed_version:
        return
    # 'output_stock_loc_id' became a related+readonly field and has been
    # replaced by 'to_output_stock_loc_id'
    queries = [
        """
            ALTER TABLE stock_warehouse_flow
            ADD COLUMN to_output_stock_loc_id INT
            REFERENCES stock_location(id)
            ON DELETE RESTRICT;
        """,
        """
            UPDATE stock_warehouse_flow
            SET to_output_stock_loc_id = output_stock_loc_id;
        """,
    ]
    for query in queries:
        cr.execute(query)
