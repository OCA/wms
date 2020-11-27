# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorMenu(Component):
    """
    Menu Structure for the client application.

    The list of menus is restricted by the profiles.
    A menu without profile is shown in every profiles.
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.menu"
    _usage = "menu"
    _expose_model = "shopfloor.menu"
    _description = __doc__

    def _get_base_search_domain(self):
        base_domain = super()._get_base_search_domain()
        return expression.AND(
            [
                base_domain,
                [
                    "|",
                    ("profile_ids", "=", False),
                    ("profile_ids", "in", self.work.profile.ids),
                ],
            ]
        )

    def _search(self, name_fragment=None):
        if not self.work.profile:
            # we need to know the warehouse of the profile
            # to load menus
            return self.env["shopfloor.menu"].browse()
        domain = self._get_base_search_domain()
        if name_fragment:
            domain.append(("name", "ilike", name_fragment))
        records = self.env[self._expose_model].search(domain)
        current_wh = self.work.profile.warehouse_id
        records = records.filtered(
            lambda menu: all(
                not pt.warehouse_id or pt.warehouse_id == current_wh
                for pt in menu.picking_type_ids
            )
        )
        return records

    def search(self, name_fragment=None):
        """List available menu entries for current profile"""
        records = self._search(name_fragment=name_fragment)
        return self._response(
            data={"size": len(records), "records": self._to_json(records)}
        )

    def _convert_one_record(self, record):
        values = record.jsonify(self._one_record_parser, one=True)
        counters = self._get_move_line_counters(record)
        values.update(counters)
        return values

    def _get_move_line_counters(self, record):
        """Lookup for all lines per menu item and compute counters.
        """
        # TODO: maybe to be improved w/ raw SQL as this run for each menu item
        # and it's called every time the menu is opened/gets refreshed
        move_line_search = self.actions_for(
            "search_move_line", picking_types=record.picking_type_ids
        )
        locations = record.picking_type_ids.mapped("default_location_src_id")
        lines_per_menu = move_line_search.search_move_lines_by_location(locations)
        return move_line_search.counters_for_lines(lines_per_menu)

    @property
    def _one_record_parser(self):
        return [
            "id",
            "name",
            "scenario",
            ("picking_type_ids:picking_types", ["id", "name"]),
        ]


class ShopfloorMenuValidator(Component):
    """Validators for the Menu endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.menu.validator"
    _usage = "menu.validator"

    def search(self):
        return {
            "name_fragment": {"type": "string", "nullable": True, "required": False}
        }


class ShopfloorMenuValidatorResponse(Component):
    """Validators for the Menu endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.menu.validator.response"
    _usage = "menu.validator.response"

    def return_search(self):
        record_schema = self._record_schema
        return self._response_schema(
            {
                "size": {"coerce": to_int, "required": True, "type": "integer"},
                "records": self.schemas._schema_list_of(record_schema),
            }
        )

    @property
    def _record_schema(self):
        schema = {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "scenario": {"type": "string", "nullable": False, "required": True},
            "picking_types": self.schemas._schema_list_of(self._picking_type_schema),
        }
        schema.update(self.schemas.move_lines_counters())
        return schema

    @property
    def _picking_type_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
