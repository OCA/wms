# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Replace collection name in log config
    env = api.Environment(cr, SUPERUSER_ID, {})
    icp = env["ir.config_parameter"].sudo()
    param = icp.get_param("rest.log.active")
    if param and "shopfloor.service" in param:
        param = param.replace("shopfloor.service", "shopfloor.app")
        icp.set_param("rest.log.active", param)
