# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import json
import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.shopfloor_base.utils import purge_endpoints, register_new_services

from .services.reception import Reception as Service

_logger = logging.getLogger(__file__)


def post_init_hook(cr, registry):
    _logger.info("Add set packaging dimension option on reception scenario")
    env = api.Environment(cr, SUPERUSER_ID, {})
    scenario = env.ref("shopfloor_reception.scenario_reception")
    options = scenario.options
    options.update({"set_packaging_dimension": True})
    scenario.options_edit = json.dumps(options)
    # The service imported is extending an existing component
    # As it is a simple python import the odoo inheritance is not working
    # So it needs to be fix
    Service._usage = "reception"
    Service._name = "shopfloor.reception"
    register_new_services(env, Service)


def uninstall_hook(cr, registry):
    _logger.info("Remove set packaging dimension option on reception scenario")
    env = api.Environment(cr, SUPERUSER_ID, {})
    scenario = env.ref("shopfloor_reception.scenario_reception")
    options = scenario.options
    if "set_packaging_dimension" in options.keys():
        options.pop("set_packaging_dimension")
    scenario.options_edit = json.dumps(options)
    Service._usage = "reception"
    purge_endpoints(env, Service._usage, endpoint="set_packaging_dimension")
