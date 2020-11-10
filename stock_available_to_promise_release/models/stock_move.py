# Copyright 2019 Camptocamp (https://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import date_utils, float_compare


class StockMove(models.Model):
    _inherit = "stock.move"

    date_priority = fields.Datetime(
        string="Priority Date",
        index=True,
        default=fields.Datetime.now,
        help="Date/time used to sort moves to deliver first. "
        "Used to calculate the ordered available to promise.",
    )
    ordered_available_to_promise = fields.Float(
        string="Ordered Available to Promise",
        compute="_compute_ordered_available_to_promise",
        search="_search_ordered_available_to_promise",
        digits="Product Unit of Measure",
        help="Available to Promise quantity minus quantities promised "
        " to older promised operations.",
    )
    release_ready = fields.Boolean(
        compute="_compute_release_ready", search="_search_release_ready",
    )
    need_release = fields.Boolean(index=True,)
    zip_code = fields.Char(related="partner_id.zip", store="True")
    city = fields.Char(related="partner_id.city", store="True")

    @api.depends(
        "ordered_available_to_promise", "picking_id.move_type", "picking_id.move_lines"
    )
    def _compute_release_ready(self):
        for move in self:
            if move.picking_id.move_type == "one":
                move.release_ready = all(
                    m.ordered_available_to_promise > 0
                    for m in move.picking_id.move_lines
                )
            else:
                move.release_ready = move.ordered_available_to_promise > 0

    @api.model
    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise UserError(_("Unsupported operator %s") % (operator,))
        moves = self.search([("ordered_available_to_promise", ">", 0)])
        moves = moves.filtered(lambda m: m.release_ready)
        return [("id", "in", moves.ids)]

    @api.depends()
    def _compute_ordered_available_to_promise(self):
        for move in self:
            move.ordered_available_to_promise = move._ordered_available_to_promise()

    @api.model
    def _search_ordered_available_to_promise(self, operator, value):
        if operator not in (">", ">=", "="):
            raise UserError(_("Unsupported operator %s") % (operator,))
        moves = self.search([("need_release", "=", True)])
        if operator == ">":
            moves = moves.filtered(lambda m: m._ordered_available_to_promise() > value)
        elif operator == ">=":
            moves = moves.filtered(lambda m: m._ordered_available_to_promise() >= value)
        else:
            moves = moves.filtered(lambda m: m._ordered_available_to_promise() == value)
        return [("id", "in", moves.ids)]

    def _should_compute_ordered_available_to_promise(self):
        return (
            self.picking_code == "outgoing"
            and self.need_release
            and not self.product_id.type == "consu"
            and not self.location_id.should_bypass_reservation()
        )

    def _action_cancel(self):
        super()._action_cancel()
        self.write({"need_release": False})
        return True

    def _ordered_available_to_promise(self):
        if not self._should_compute_ordered_available_to_promise():
            return 0.0
        available = self.product_id.with_context(
            **self._order_available_to_promise_qty_ctx()
        ).qty_available
        return max(
            min(available - self._previous_promised_qty(), self.product_qty), 0.0
        )

    def _order_available_to_promise_qty_ctx(self):
        return {
            # used by product qty calculation in stock module
            # (all the way down to `_get_domain_locations`).
            "location": self.warehouse_id.lot_stock_id.id,
        }

    def _promise_reservation_horizon(self):
        return self.env.company.sudo().stock_reservation_horizon

    def _promise_reservation_horizon_date(self):
        horizon = self._promise_reservation_horizon()
        if horizon:
            # start from end of today and add horizon days
            return date_utils.add(
                date_utils.end_of(fields.Datetime.today(), "day"), days=horizon
            )
        return None

    def _previous_promised_quantity_domain(self):
        """Lookup for product promised qty in the same warehouse.

        Moves to consider are either already released or still be to released
        but not done yet. Each of them should fit the reservation horizon.
        """
        base_domain = [
            ("product_id", "=", self.product_id.id),
            ("warehouse_id", "=", self.warehouse_id.id),
        ]
        horizon_date = self._promise_reservation_horizon_date()
        if horizon_date:
            # exclude moves planned beyond the horizon
            base_domain.append(("date_expected", "<=", horizon_date))

        # either the move has to be released
        # and priority is higher than the current one
        domain_not_released = [
            ("need_release", "=", True),
            "|",
            ("priority", ">", self.priority),
            "&",
            ("date_priority", "<", self.date_priority),
            ("priority", "=", self.priority),
        ]
        # or it has been released already
        # and is not canceled or done
        domain_released = [
            ("need_release", "=", False),
            (
                "state",
                "in",
                ("waiting", "confirmed", "partially_available", "assigned"),
            ),
        ]
        # NOTE: this domain might be suboptimal as we may lookup too many moves.
        # If we face performance issues, this is a good candidate to debug.
        return expression.AND(
            [base_domain, expression.OR([domain_not_released, domain_released])]
        )

    def _previous_promised_qty(self):
        previous_moves = self.search(
            expression.AND(
                # TODO: `!=` could be suboptimal, consider filter out on recordset
                [self._previous_promised_quantity_domain(), [("id", "!=", self.id)]]
            ),
        )
        # TODO: consider sum via SQL
        promised_qty = sum(
            previous_moves.mapped(
                lambda move: max(move.product_qty - move.reserved_availability, 0.0)
            )
        )
        return promised_qty

    def release_available_to_promise(self):
        self._run_stock_rule()

    def _prepare_move_split_vals(self, qty):
        vals = super()._prepare_move_split_vals(qty)
        # The method set procure_method as 'make_to_stock' by default on split,
        # but we want to keep 'make_to_order' for chained moves when we split
        # a partially available move in _run_stock_rule().
        if self.env.context.get("release_available_to_promise"):
            vals.update({"procure_method": self.procure_method, "need_release": True})
        return vals

    def _run_stock_rule(self):
        """Launch procurement group run method with remaining quantity

        As we only generate chained moves for the quantity available minus the
        quantity promised to older moves, to delay the reservation at the
        latest, we have to periodically retry to assign the remaining
        quantities.
        """
        precision = self.env["decimal.precision"].precision_get(
            "Product Unit of Measure"
        )
        procurement_requests = []
        pulled_moves = self.env["stock.move"]
        backorder_links = {}
        for move in self:
            if not move.need_release:
                continue
            if move.state not in ("confirmed", "waiting"):
                continue
            # do not use the computed field, because it will keep
            # a value in cache that we cannot invalidate declaratively
            available_quantity = move._ordered_available_to_promise()
            if float_compare(available_quantity, 0, precision_digits=precision) <= 0:
                continue

            quantity = min(move.product_qty, available_quantity)
            remaining = move.product_qty - quantity

            if float_compare(remaining, 0, precision_digits=precision) > 0:
                if move.picking_id.move_type == "one":
                    # we don't want to deliver unless we can deliver all at
                    # once
                    continue
                new_move = move._release_split(remaining)
                backorder_links[new_move.picking_id] = move.picking_id

            values = move._prepare_procurement_values()
            procurement_requests.append(
                self.env["procurement.group"].Procurement(
                    move.product_id,
                    move.product_uom_qty,
                    move.product_uom,
                    move.location_id,
                    move.rule_id and move.rule_id.name or "/",
                    move.origin,
                    move.company_id,
                    values,
                )
            )
            pulled_moves |= move

        # move the unreleased moves to a backorder
        released_pickings = pulled_moves.picking_id
        unreleased_moves = released_pickings.move_lines - pulled_moves
        for unreleased_move in unreleased_moves:
            # no split will occur as we keep the same qty, but the move
            # will be assigned to a new stock.picking
            original_picking = unreleased_move.picking_id
            unreleased_move._release_split(unreleased_move.product_qty)
            backorder_links[unreleased_move.picking_id] = original_picking

        for backorder, origin in backorder_links.items():
            backorder._release_link_backorder(origin)

        self.env["procurement.group"].run_defer(procurement_requests)

        # Set all transfers released to "printed", consider the work has
        # been planned and started and another "release" of moves should
        # (for instance) merge new pickings with this "round of release".
        pulled_moves._release_assign_moves()
        pulled_moves._release_set_printed()

        return True

    def _release_set_printed(self):
        picking_ids = set()
        moves = self
        while moves:
            picking_ids.update(moves.mapped("picking_id").ids)
            moves = moves.mapped("move_orig_ids")
        pickings = self.env["stock.picking"].browse(picking_ids)
        pickings.filtered(lambda p: not p.printed).printed = True

    def _release_assign_moves(self):
        moves = self
        while moves:
            moves._action_assign()
            moves = moves.mapped("move_orig_ids")

    def _release_split(self, remaining_qty):
        """Split move and create a new picking for it.

        Instead of splitting the move and leave remaining qty into the same picking
        we move it to a new one so that we can release it later as soon as
        the qty is available.
        """
        context = self.env.context
        self = self.with_context(release_available_to_promise=True)
        # Rely on `printed` flag to make _assign_picking create a new picking.
        # See `stock.move._assign_picking` and
        # `stock.move._search_picking_for_assignation`.
        if not self.picking_id.printed:
            self.picking_id.printed = True
        new_move = self.browse(self._split(remaining_qty))
        # Picking assignment is needed here because `_split` copies the move
        # thus the `_should_be_assigned` condition is not satisfied
        # and the move is not assigned.
        new_move._assign_picking()
        return new_move.with_context(context)
