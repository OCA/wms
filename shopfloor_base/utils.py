# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
# @author Simone Orsi <simahawk@gmail.com>
import logging
import os
from functools import wraps

from odoo.modules.module import load_information_from_description_file
from odoo.tools.config import config as odoo_config

from odoo.addons.base_rest.controllers.main import _PseudoCollection
from odoo.addons.component.core import WorkContext, _component_databases

_logger = logging.getLogger(__name__)


def ensure_model(model_name):
    """Decorator to ensure data method is called w/ the right recordset."""

    def _ensure_model(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            # 1st arg is `self`
            record = args[1]
            if record is not None:
                assert (
                    record._name == model_name
                ), f"Expected model: {model_name}. Got: {record._name}"
            return func(*args, **kwargs)

        return wrapped

    return _ensure_model


APP_VERSIONS = {}


def get_version(module_name, module_path=None):
    """Return module version straight from manifest."""
    global APP_VERSIONS
    if APP_VERSIONS.get(module_name):
        return APP_VERSIONS[module_name]
    try:
        info = load_information_from_description_file(module_name, mod_path=module_path)
        APP_VERSIONS[module_name] = info["version"]
        return APP_VERSIONS[module_name]
    except Exception:
        return "dev"


APP_VERSION = get_version("shopfloor_mobile_base")


def _get_running_env():
    """Retrieve current system environment.

    Expected key `RUNNING_ENV` is compliant w/ `server_environment` naming
    but is not depending on it.

    Additionally, as specific key for Shopfloor is supported.

    You don't need `server_environment` module to have this feature.
    """
    for key in ("SHOPFLOOR_RUNNING_ENV", "RUNNING_ENV"):
        if os.getenv(key):
            return os.getenv(key)
        if odoo_config.options.get(key.lower()):
            return odoo_config.get(key.lower())
    return "prod"


RUNNING_ENV = _get_running_env()


def register_new_services(env, *component_classes, apps=None):
    """Enforce registration of new services straight from their classes.

    At some stage (eg: a post install hook) the component registry
    might not be fully loaded and the components might be not fully "ready".
    For this reason, not all the inherited properties
    are granted to be available (eg: _collection)
    and they won't be available for `components_registry.lookup` call.

    This is why, to ensure that the new services endpoints
    are registered in any case we prepare their classes "manually" here
    and pass them over to sf.app._get_services.

    In this way, if their endpoint_route rows are not there
    they will be generated on the fly,

    Please, note that this func is very low level
    and must be used only in particular situations (such as install hooks).
    """
    if odoo_config["test_enable"]:
        # When installing modules for tests, there's nothing to do.
        # Moreover, it can lead to weird service behavior
        # because the classes will be decorated
        # but when they are not fully ready.
        return
    components = load_components_without_registry(env, *component_classes)
    if not components:
        return
    apps = apps or env["shopfloor.app"].search([])
    apps.with_context(sf_service_components=components)._register_controllers()


def load_components_without_registry(env, *component_classes):
    """Prepare components' instances w/o real registry lookup."""
    collection = _PseudoCollection("shopfloor.app", env)
    rest_service = env["rest.service.registration"]
    if not _component_databases.get(env.cr.dbname):
        # no registry ready yet (eg: install via cmd line, tests, etc)
        _logger.info("component registry not ready yet")
        return []
    work = WorkContext(model_name=rest_service._name, collection=collection)
    return [comp(work) for comp in component_classes]


def purge_endpoints(env, service_usage, endpoint=None):
    """Remove stale services' endpoints routes.

    When scenario are removed (eg: module uninstalled)
    their routes must be cleaned up.
    You can use this function to easily clean them for all apps.

    Motivation: registered routes for a given app are taken
    from the endpoint_route table via `route_group`.
    As the table is populated dynamically with registered components
    when a component is removed there's no direct update to the table.
    Hence, is the responsibility of the dev to take care of the cleanup.
    """
    apps = env["shopfloor.app"].search([])
    for app in apps:
        route = app.api_url_for_service(service_usage, endpoint=endpoint)
        route = route + ("/" if not endpoint else "")
        env.cr.execute("DELETE FROM endpoint_route WHERE route like %s", (f"{route}%",))
