# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

import logging

from werkzeug.exceptions import Forbidden

from odoo.addons.component.core import AbstractComponent

_logger = logging.getLogger(__name__)


class BaseShopfloorService(AbstractComponent):
    _inherit = "base.shopfloor.service"

    def dispatch(self, method_name, *args, params=None):
        self._validate_request(self.request)
        return super().dispatch(method_name, *args, params=params)

    def _validate_request(self, request):
        if self.collection.auth_type == "api_key":
            # request api key is already validated when we reach this point
            # Now let's validate it at app level.
            if (
                self.request.auth_api_key_id
                not in self.collection.sudo()._allowed_api_key_ids()
            ):
                _logger.error(
                    "API key not allowed on app '%s'", self.collection.tech_name
                )
                raise Forbidden()
