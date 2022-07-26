# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    domain = [("registry_sync", "=", False)]
    env["shopfloor.app"].search(domain).write({"registry_sync": True})
    _logger.info("Activate sync for existing apps")
