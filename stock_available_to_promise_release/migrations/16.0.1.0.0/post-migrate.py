# Copyright 2022 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info(
        "stock_available_to_promise_release: Configure picking types"
        " to prevent new moves into released pickings"
    )
    cr.execute("update stock_picking_type set prevent_new_move_after_release = true")
