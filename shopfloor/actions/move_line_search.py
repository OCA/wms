# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component


class MoveLineSearch(Component):
    """Provide methods to search move line records.

    The methods should be used in Service Components, so a search will always
    have the same result in all scenarios.
    """

    _name = "shopfloor.search.move.line"
    _inherit = "shopfloor.process.action"
    _usage = "search_move_line"

    @property
    def picking_types(self):
        return getattr(
            self.work, "picking_types", self.env["stock.picking.type"].browse()
        )

    def _search_move_lines_by_location_domain(
        self,
        locations,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        match_user=False,
        picking_ready=True,
    ):
        domain = [
            ("location_id", "child_of", locations.ids),
            ("qty_done", "=", 0),
            ("state", "in", ("assigned", "partially_available")),
        ]
        if picking_type:
            # auto_join in place for this field
            domain += [("picking_id.picking_type_id", "=", picking_type.id)]
        elif self.picking_types:
            domain += [("picking_id.picking_type_id", "in", self.picking_types.ids)]
        if package:
            domain += [("package_id", "=", package.id)]
        if product:
            domain += [("product_id", "=", product.id)]
        if lot:
            domain += [("lot_id", "=", lot.id)]
        if match_user:
            domain += [
                "|",
                ("shopfloor_user_id", "=", False),
                ("shopfloor_user_id", "=", self.env.uid),
            ]
        if picking_ready:
            domain += [("picking_id.state", "=", "assigned")]
        return domain

    def search_move_lines_by_location(
        self,
        locations,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        order="priority",
        match_user=False,
        sort_keys_func=None,
        picking_ready=True,
    ):
        """Find lines that potentially need work in given locations."""
        move_lines = self.env["stock.move.line"].search(
            self._search_move_lines_by_location_domain(
                locations,
                picking_type,
                package,
                product,
                lot,
                match_user=match_user,
                picking_ready=picking_ready,
            )
        )
        sort_keys_func = sort_keys_func or self._sort_key_move_lines(order)
        move_lines = move_lines.sorted(sort_keys_func)
        return move_lines

    @staticmethod
    def _sort_key_move_lines(order):
        """Return a sorting function to order lines."""

        if order == "priority":
            # make prority negative to keep sorting ascending
            return lambda line: (
                -int(line.move_id.priority or "0"),
                line.move_id.date,
            )
        elif order == "location":
            return lambda line: (
                line.location_id.shopfloor_picking_sequence or "",
                line.location_id.name,
                line.move_id.date,
            )
        return lambda line: line

    def counters_for_lines(self, lines):
        # Not using mapped/filtered to support simple lists and generators
        priority_lines = [x for x in lines if int(x.picking_id.priority or "0") > 0]
        return {
            "lines_count": len(lines),
            "picking_count": len({x.picking_id.id for x in lines}),
            "priority_lines_count": len(priority_lines),
            "priority_picking_count": len({x.picking_id.id for x in priority_lines}),
        }
