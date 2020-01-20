from odoo.addons.base_rest.controllers import main
import json


class ShopfloorController(main.RestController):
    _root_path = "/shopfloor/"
    _collection_name = "shopfloor.services"
    _default_auth = "api_key"



