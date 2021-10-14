# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo.addons.shopfloor_base.controllers.main import ShopfloorController

# Do not extend the existing controller to not cause this error:
#
# odoo.addons.base_rest.models.rest_service_registration:
# Only one REST controller can be safely declared for root path /shopfloor/
ShopfloorController._default_auth = "api_key"
