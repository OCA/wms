# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Simone Orsi <simone.orsi@camptocamp.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.modules.module import load_information_from_description_file

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
