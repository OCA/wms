# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class BaseShopfloorSchemaResponse(Component):
    """Provide methods to share schema structures

    The methods should be used in Service Components, so we try to
    have similar schema structures across scenarios.
    """

    _inherit = "base.rest.service"
    _name = "base.shopfloor.schemas"
    _collection = "shopfloor.service"
    _usage = "schema"
    _is_rest_service_component = False

    def _schema_list_of(self, schema, **kw):
        schema = {
            "type": "list",
            "nullable": True,
            "required": True,
            "schema": {"type": "dict", "schema": schema},
        }
        schema.update(kw)
        return schema

    def _simple_record(self, **kw):
        schema = {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
        schema.update(kw)
        return schema

    def _schema_dict_of(self, schema, **kw):
        schema = {
            "type": "dict",
            "nullable": True,
            "required": True,
            "schema": schema,
        }
        schema.update(kw)
        return schema

    def _schema_search_results_of(self, schema, **kw):
        return {
            "size": {"required": True, "type": "integer"},
            "records": {
                "type": "list",
                "required": True,
                "schema": {"type": "dict", "schema": schema},
            },
        }

    def menu_item_counters(self, **kw):
        return {}
