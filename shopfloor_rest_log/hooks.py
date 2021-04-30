# Copyright 2021 ACSONE SA/NV
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("Enabling DB logging for Shopfloor app")
    env = api.Environment(cr, SUPERUSER_ID, {})
    params = env["ir.config_parameter"].sudo()
    key = "rest.log.active"
    shopfloor_value = "shopfloor.service"
    param = params.search([("key", "=", key)], limit=1)
    if param:
        value = (param.value if param.value else "").split(",")
        if shopfloor_value not in param:
            value.append(shopfloor_value)
            param.value = ",".join([x.strip() for x in value if x.strip()])
    else:
        params.create({"key": key, "value": shopfloor_value})
