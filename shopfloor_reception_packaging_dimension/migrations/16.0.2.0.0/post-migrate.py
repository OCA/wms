# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import json
import logging

from odoo.upgrade.util import env as Env

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = Env(cr)
    _logger.info("Add create new packaging option on reception scenario")
    scenario = env.ref("shopfloor_reception.scenario_reception")
    options = scenario.options
    options.update({"create_new_packaging": True})
    scenario.options_edit = json.dumps(options)
