# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    module = env["ir.module.module"].search(
        [("name", "=", "shopfloor_mobile_base_auth_api_key")]
    )
    if module.state == "uninstalled":
        # Auth has been decoupled
        # but existing installations might depend on api key.
        _logger.info("Install shopfloor_mobile_base_auth_api_key")
        module.write({"state": "to install"})
