# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


def migrate(cr, version):
    if not version:
        return
    query = """
        UPDATE ir_model_data
        SET module='shopfloor_manual_product_transfer'
        WHERE module='shopfloor'
        AND name = 'scenario_manual_product_transfer';
    """
    cr.execute(query)
