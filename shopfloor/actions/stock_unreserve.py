# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.addons.component.core import Component


class StockUnreserve(Component):
    """Provide methods to unreserve goods of a location."""

    _name = "shopfloor.stock.unreserve.action"
    _inherit = "shopfloor.process.action"
    _usage = "stock.unreserve"

    def check_unreserve(self, location, move_lines, product=None, lot=None):
        """Return a message if there is an ongoing operation in the location.

        It could be a move line with some qty already processed or another
        Shopfloor user working there.

        :param location: stock location from which moves are unreserved
        :param move_lines: move lines to unreserve
        :param product: optional product to limit the scope in the location
        """
        location_move_lines = self._find_location_all_move_lines(location, product, lot)
        extra_move_lines = location_move_lines - move_lines
        if extra_move_lines:
            return self.msg_store.picking_already_started_in_location(
                extra_move_lines.picking_id
            )

    def unreserve_moves(self, move_lines, picking_types):
        """Unreserve moves from `move_lines'.

        Returns a tuple of (
          move lines that stays in the location to process,
          moves to reserve again
        )
        """
        moves_to_unreserve = move_lines.move_id
        # If there is no other moves to unreserve of a different picking type, leave
        lines_other_picking_types = move_lines.filtered(
            lambda line: line.picking_id.picking_type_id not in picking_types
        )
        if not lines_other_picking_types:
            return (move_lines, self.env["stock.move"].browse())
        # if we leave the package level around, it will try to reserve
        # the same package as before
        package_levels = move_lines.package_level_id
        package_levels.explode_package()
        moves_to_unreserve._do_unreserve()
        return (move_lines - lines_other_picking_types, moves_to_unreserve)

    def _find_location_all_move_lines_domain(self, location, product=None, lot=None):
        domain = [
            ("location_id", "=", location.id),
            ("state", "in", ("assigned", "partially_available")),
        ]
        if product:
            domain.append(("product_id", "=", product.id))
        if lot:
            domain.append(("lot_id", "=", lot.id))
        return domain

    def _find_location_all_move_lines(self, location, product=None, lot=None):
        return self.env["stock.move.line"].search(
            self._find_location_all_move_lines_domain(location, product, lot)
        )
