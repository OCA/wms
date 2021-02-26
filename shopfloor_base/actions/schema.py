# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.component.core import Component


class SchemaAction(Component):
    """Provide methods to share schema structures

    The methods should be used in Service Components, so we try to
    have similar schema structures across scenario.
    """

    _inherit = "shopfloor.process.action"
    _name = "shopfloor.schema.action"
    _usage = "schema"

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
