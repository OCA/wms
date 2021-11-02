# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    # Auth have been decoupled and split to `shopfloor_mobile_base_auth_api_key`
    # for api key support.
    # Since this is the base auth everyone used so far,
    # let's make sure we don't break existing installations if any.
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search(
        [
            ("name", "=", "shopfloor_mobile_base_auth_api_key"),
            ("state", "=", "uninstalled"),
        ]
    )
    if module:
        _logger.info("Install module shopfloor_mobile_base_auth_api_key")
        module.write({"state": "to install"})
    return
