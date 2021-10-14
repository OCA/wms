# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.base_rest.controllers import main


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/<tech_name(shopfloor.app):collection>/"
    # Useless when calling via real request
    # as the collection will come from model converter
    _collection_name = "shopfloor.app"
    _default_auth = "user"
