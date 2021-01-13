# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    cr.execute(
        """
       SELECT shopfloor_menu_id, shopfloor_profile_id
       FROM shopfloor_menu_shopfloor_profile_rel
    """
    )
    menu_profile_ids = {}
    for menu_id, profile_id in cr.fetchall():
        menu_profile_ids.setdefault(menu_id, [])
        menu_profile_ids[menu_id].append(profile_id)

    for menu_id, profile_ids in menu_profile_ids.items():
        if len(profile_ids) > 1:
            _logger.warn(
                "menu id %s was linked with 2 profiles (ids: %s),"
                " only one is now possible now, menu has been"
                " duplicated for each profile",
                menu_id,
                profile_ids,
            )
        index = 1
        for profile_id in profile_ids:
            menu = env["shopfloor.menu"].browse(menu_id)
            if index > 1:
                menu = menu.copy({"name": "{} ({})".format(menu.name, index)})
            menu.profile_id = profile_id
            index += 1
