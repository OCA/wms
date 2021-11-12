# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def post_init_hook(cr, registry):
    _logger.info("Update ref field if empty to match id")
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Update ref field
    partners = env["res.partner"].search([("ref", "=", False)])
    for partner in partners:
        partner.ref = partner.id
