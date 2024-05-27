# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("Remove original 'Unblock Release' server action...")
    env = api.Environment(cr, SUPERUSER_ID, {})
    action = env.ref(
        "stock_available_to_promise_release_block.action_stock_move_unblock_release",
        raise_if_not_found=False,
    )
    action.unlink()
