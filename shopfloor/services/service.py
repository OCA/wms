from odoo import _
from odoo.exceptions import MissingError
from odoo.osv import expression

from odoo.addons.component.core import AbstractComponent


class BaseShopfloorService(AbstractComponent):
    """Base class for REST services"""

    _inherit = "base.rest.service"
    _name = "base.shopfloor.service"
    _collection = "shopfloor.service"
    _expose_model = None

    def _get(self, _id):
        domain = expression.normalize_domain(self._get_base_search_domain())
        domain = expression.AND([domain, [("id", "=", _id)]])
        record = self.env[self._expose_model].search(domain)
        if not record:
            raise MissingError(
                _("The record %s %s does not exist") % (self._expose_model, _id)
            )
        else:
            return record

    def _get_base_search_domain(self):
        return []

    def _convert_one_record(self, record):
        """To implement in service Components"""
        return {}

    def _to_json(self, records):
        res = []
        for record in records:
            res.append(self._convert_one_record(record))
        return res

    def _get_openapi_default_parameters(self):
        defaults = super()._get_openapi_default_parameters()
        demo_api_key = self.env.ref(
            "shopfloor.api_key_demo", raise_if_not_found=False
        ).key
        defaults.extend(
            [
                {
                    "name": "API-KEY",
                    "in": "header",
                    "description": "API key for Authorization",
                    "required": True,
                    "schema": {"type": "string"},
                    "style": "simple",
                    "value": demo_api_key,
                },
                {
                    "name": "SERVICE_CTX_MENU_ID",
                    "in": "header",
                    "description": "ID of the current menu",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": "1",
                },
                {
                    "name": "SERVICE_CTX_PROFILE_ID",
                    "in": "header",
                    "description": "ID of the current profile",
                    "required": True,
                    "schema": {"type": "integer"},
                    "style": "simple",
                    "value": "1",
                },
            ]
        )
        return defaults
