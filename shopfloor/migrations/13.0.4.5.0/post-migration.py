# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})

    _logger.info("Update zone picking settings")
    zp = env.ref("shopfloor.scenario_zone_picking", raise_if_not_found=False)
    if zp:
        options = zp.options
        if "pick_pack_same_time" not in options:
            options.update({"pick_pack_same_time": True})
        zp.options_edit = json.dumps(options)
