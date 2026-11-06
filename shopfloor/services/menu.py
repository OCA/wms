# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class ShopfloorMenu(Component):
    _inherit = "shopfloor.service.menu"

    def _convert_one_record(self, record):
        values = super()._convert_one_record(record)
        shopfloor_app = self.work.collection
        if record.picking_type_ids:
            if shopfloor_app.show_counters:
                counters = self._get_move_line_counters(record)
                values.update(counters)
            else:
                values.update()
                values["has_work"] = self._has_work_to_do(record)
        return values

    def _has_work_to_do(self, record):
        """Fast existence check to verify if work is pending without computing counters."""
        move_line_search = self._actions_for(
            "search_move_line",
            picking_types=record.picking_type_ids,
            additional_domain=record.move_line_search_additional_domain,
            sort_order=record.move_line_search_sort_order,
            sort_order_custom_code=record.move_line_search_sort_order_custom_code,
        )
        domain = move_line_search._search_move_lines_domain()
        return bool(self.env["stock.move.line"].search_count(domain, limit=1))

    def _get_move_line_counters(self, record):
        """Lookup for all lines per menu item and compute counters."""
        # TODO: maybe to be improved w/ raw SQL as this run for each menu item
        # and it's called every time the menu is opened/gets refreshed
        move_line_search = self._actions_for(
            "search_move_line",
            picking_types=record.picking_type_ids,
            additional_domain=record.move_line_search_additional_domain,
            sort_order=record.move_line_search_sort_order,
            sort_order_custom_code=record.move_line_search_sort_order_custom_code,
        )
        lines_per_menu = move_line_search.search_move_lines()
        return move_line_search.counters_for_lines(lines_per_menu)

    def _one_record_parser(self, record):
        parser = super()._one_record_parser(record)
        if not record.picking_type_ids:
            return parser
        return parser + [
            ("picking_type_ids:picking_types", ["id", "name"]),
        ]


class ShopfloorMenuValidatorResponse(Component):
    """Validators for the Menu endpoints responses"""

    _inherit = "shopfloor.service.menu.validator.response"

    @property
    def _record_schema(self):
        schema = super()._record_schema
        schema.update(
            {
                "picking_types": self.schemas._schema_list_of(
                    self._picking_type_schema, required=False, nullable=True
                ),
                "has_work": {"type": "boolean", "nullable": True, "required": False},
            }
        )
        schema.update(self.schemas.move_lines_counters())
        return schema

    @property
    def _picking_type_schema(self):
        return {
            "id": {"coerce": to_int, "required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
        }
