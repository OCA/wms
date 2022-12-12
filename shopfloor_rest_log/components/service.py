# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# @author Guewen Baconnier <guewen.baconnier@camptocamp.com>
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).


from odoo.addons.rest_log.components.service import BaseRESTService
from odoo.addons.shopfloor_base.exceptions import ShopfloorError


class ShopfloorRESTService(BaseRESTService):
    _inherit = "base.rest.service"

    def _dispatch_exception(
        self, method_name, exception_klass, orig_exception, *args, params=None
    ):
        try:
            super()._dispatch_exception(
                method_name, exception_klass, orig_exception, *args, params=params
            )
        except Exception as e:
            if isinstance(orig_exception, ShopfloorError):
                raise orig_exception
            else:
                raise e
