# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return

    env = api.Environment(cr, SUPERUSER_ID, {})
    records = env["rest.log"].search([("headers", "ilike", "%App-Version%")])
    if records:
        _logger.info("Computing real_uid and app_version for %s records", len(records))
    for rec in records:
        rec.update(_get_vals(json.loads(rec.headers)))


def _get_vals(headers):
    user_id = headers.get("App-User-Id", "0")
    vals = {
        "real_uid": int(user_id)
        if isinstance(user_id, str) and user_id.isdigit()
        else None,
        "app_version": headers.get("App-Version", "Unknown"),
    }
    return vals
