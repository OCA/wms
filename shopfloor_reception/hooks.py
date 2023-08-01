# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging

from odoo import SUPERUSER_ID, api

from odoo.addons.shopfloor_base.utils import purge_endpoints, register_new_services

from .services.reception import Reception as Service

_logger = logging.getLogger(__file__)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Register routes for %s", Service._usage)
    register_new_services(env, Service)


def uninstall_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    _logger.info("Refreshing routes for existing apps")
    purge_endpoints(env, Service._usage)
