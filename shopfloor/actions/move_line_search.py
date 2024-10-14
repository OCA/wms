# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2024 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tools import safe_eval

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

    @property
    def additional_domain(self):
        return getattr(self.work, "additional_domain", [])

    @property
    def sort_order(self):
        return getattr(self.work, "sort_order", "priority")

    @property
    def sort_order_custom_code(self):
        return getattr(self.work, "sort_order_custom_code", None)

    def _get_additional_domain_eval_context(self):
        """Prepare the context used when evaluating the additional domain
        :returns: dict -- evaluation context given to safe_eval
        """
        return {
            "datetime": safe_eval.datetime,
            "dateutil": safe_eval.dateutil,
            "time": safe_eval.time,
            "uid": self.env.uid,
            "user": self.env.user,
        }

    def _sort_key_custom_code_eval_context(self, line):
        return {
            "line": line,
            "key": None,
            "get_sort_key_priority": self._sort_key_move_lines_priority,
            "get_sort_key_location": self._sort_key_move_lines_location,
            "get_sort_key_assigned_to_current_user": self._sort_key_assigned_to_current_user,
        }

    def _search_move_lines_domain(
        self,
        locations=None,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        match_user=False,
        picking_ready=True,
        # When True, adds the package in the domain even if the package is False
        enforce_empty_package=False,
    ):
        """Return a domain to search move lines.

        Be careful on the use of the picking_type parameter. This paramater can take
        a recordset or None as value. The interpretation of the value is as follows:
        * If picking_type is None, the domain will be filtered on all picking types
            defined in the work. (most probably those defined on the menu)
        * If picking_type is a recordset, the domain will be filtered on the given
            picking types if the recordset is not empty. If the recordset is empty,
            the domain will not be filtered on any picking type.
        """
        domain = [
            ("qty_done", "=", 0),
            ("state", "in", ("assigned", "partially_available")),
        ]
        picking_types = picking_type if picking_type is not None else self.picking_types
        if picking_types:
            domain += [("picking_id.picking_type_id", "in", picking_types.ids)]
        locations = locations or picking_types.default_location_src_id
        if locations:
            domain += [("location_id", "child_of", locations.ids)]
        if package or package is not None and enforce_empty_package:
            domain += [("package_id", "=", package.id if package else False)]
        if product:
            domain += [("product_id", "=", product.id)]
        if lot:
            domain += [("lot_id", "=", lot.id)]
        if match_user:
            # we only want to see the lines assigned to the current user
            domain += [
                ("shopfloor_user_id", "in", (False, self.env.uid)),
                ("picking_id.user_id", "in", (False, self.env.uid)),
            ]
        if picking_ready:
            domain += [("picking_id.state", "=", "assigned")]
        if self.additional_domain:
            eval_context = self._get_additional_domain_eval_context()
            domain += safe_eval.safe_eval(self.additional_domain, eval_context)
        return domain

    def search_move_lines(
        self,
        locations=None,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        order=None,
        match_user=False,
        sort_keys_func=None,
        picking_ready=True,
        enforce_empty_package=False,
    ):
        """Find lines that potentially need work in given locations."""
        move_lines = self.env["stock.move.line"].search(
            self._search_move_lines_domain(
                locations,
                picking_type,
                package,
                product,
                lot,
                match_user=match_user,
                picking_ready=picking_ready,
                enforce_empty_package=enforce_empty_package,
            )
        )
        order = order or self.sort_order
        sort_keys_func = sort_keys_func or self._sort_key_move_lines(order)
        move_lines = move_lines.sorted(sort_keys_func)
        return move_lines

    def _sort_key_move_lines(self, order=None):
        """Return a sorting function to order lines."""
        if order is None:
            return lambda line: tuple()

        if order == "priority":
            return self._sort_key_move_lines_priority

        if order == "location":
            return self._sort_key_move_lines_location

        if order == "custom_code":
            return self._sort_key_custom_code

        if order == "assigned_to_current_user":
            return self._sort_key_assigned_to_current_user

        raise ValueError(f"Unknown order '{order}'")

    def _sort_key_move_lines_priority(self, line):
        # make prority negative to keep sorting ascending
        return self._sort_key_assigned_to_current_user(line) + (
            -int(line.move_id.priority or "0"),
            line.move_id.date,
            line.move_id.id,
        )

    def _sort_key_move_lines_location(self, line):
        return self._sort_key_assigned_to_current_user(line) + (
            line.location_id.shopfloor_picking_sequence or "",
            line.location_id.name,
            line.move_id.date,
            line.move_id.id,
        )

    def _sort_key_assigned_to_current_user(self, line):
        user_id = line.shopfloor_user_id.id or line.picking_id.user_id.id or None
        # Determine sort priority
        # Priority 0: Assigned to the current user
        # Priority 1: Not assigned to any user
        # Priority 2: Assigned to a different user
        if user_id == self.env.uid:
            priority = 0
        elif user_id is None:
            priority = 1
        else:
            priority = 2
        return (priority,)

    def _sort_key_custom_code(self, line):
        context = self._sort_key_custom_code_eval_context(line)
        safe_eval.safe_eval(
            self.sort_order_custom_code, context, mode="exec", nocopy=True
        )
        return context["key"]

    def counters_for_lines(self, lines):
        # Not using mapped/filtered to support simple lists and generators
        priority_lines = set()
        priority_pickings = set()
        for line in lines:
            if int(line.move_id.priority or "0") > 0:
                priority_lines.add(line)
            if int(line.picking_id.priority or "0") > 0:
                priority_pickings.add(line.picking_id)
        return {
            "lines_count": len(lines),
            "picking_count": len({x.picking_id.id for x in lines}),
            "priority_lines_count": len(priority_lines),
            "priority_picking_count": len(priority_pickings),
        }
