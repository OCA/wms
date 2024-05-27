# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    remove_unblock_release_ir_action_server(cr)


def remove_unblock_release_ir_action_server(cr):
    # The same XML-ID will be used by a new window action to open a wizard
    _logger.info("Remove action 'action_sale_order_line_unblock_release'")
    queries = [
        """
            DELETE FROM ir_act_server
            WHERE id IN (
                SELECT res_id
                FROM ir_model_data
                WHERE module='sale_stock_available_to_promise_release_block'
                AND name='action_sale_order_line_unblock_release'
                AND model='ir.actions.server'
            );
        """,
        """
            DELETE FROM ir_model_data
            WHERE module='sale_stock_available_to_promise_release_block'
            AND name='action_sale_order_line_unblock_release';
        """,
    ]
    for query in queries:
        cr.execute(query)
