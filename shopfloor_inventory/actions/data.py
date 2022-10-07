# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("stock.inventory.location")
    def inventory_location(self, record, **kw):
        return self._jsonify(record, self._inventory_location_parser, **kw)

    def inventory_locations(self, record, **kw):
        return self.inventory_location(record, multi=True)

    @property
    def _inventory_location_parser(self):
        return [("location_id:location", self._location_parser), "state"]

    @ensure_model("stock.inventory")
    def inventory(self, record, with_locations=False, **kw):
        parser = self._inventory_parser
        if with_locations:
            parser.append(
                ("sub_location_ids:locations", self._inventory_location_parser)
            )
        return self._jsonify(record, parser, **kw)

    def inventories(self, record, with_locations=False, **kw):
        return self.inventory(record, with_locations=with_locations, multi=True)

    @property
    def _inventory_parser(self):
        return [
            "id",
            "name",
            "date",
            "location_count",
            "remaining_location_count",
            "inventory_line_count",
        ]

    @ensure_model("stock.inventory.line")
    def inventory_line(self, record, **kw):
        if not record:
            record = self.env["stock.inventory.line"]
        return self._jsonify(record, self._inventory_line_parser, **kw)

    def inventory_lines(self, record, **kw):
        return self.inventory_line(record, multi=True)

    @property
    def _inventory_line_parser(self):
        return [
            "id",
            "product_qty",
            "theoretical_qty",
            ("prod_lot_id:lot", self._lot_parser),
            ("product_id:product", self._product_parser),
            ("location_id:location", self._location_parser),
            ("package_id:package", self._package_parser),
        ]
