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
    _logger.info(
        "stock_available_to_promise_release: Set last release date on some pickings"
    )
    cr.execute(
        """
with picks as (
    select sp.id  from stock_picking sp
        left join stock_picking_type spt on sp.picking_type_id = spt.id
        left join stock_move sm on  sm.picking_id = sp.id
        left join stock_rule sr on sr.id = sm.rule_id
        where sp.printed = true and spt.code = 'outgoing'
            and sr.available_to_promise_defer_pull = true
        group by sp.id
)
update stock_picking
    set last_release_date = create_date
    from picks
    where stock_picking.id = picks.id
        and last_release_date is null
    """
    )
