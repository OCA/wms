# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.info("Give Shopfloor rights to Stock users")
    stock_user_group = env.ref("stock.group_stock_user")
    stock_mngr_group = env.ref("stock.group_stock_manager")
    stock_user_group.implied_ids += env.ref("shopfloor_base.group_shopfloor_user")
    stock_mngr_group.implied_ids += env.ref("shopfloor_base.group_shopfloor_manager")
