# Copyright 2019-2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
import itertools
import logging
import operator as py_operator

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools import date_utils, float_compare, float_round

_logger = logging.getLogger(__name__)


class StockMove(models.Model):
    _inherit = "stock.move"

    date_priority = fields.Datetime(
        string="Priority Date",
        index=True,
        default=fields.Datetime.now,
        help="Date/time used to sort moves to deliver first. "
        "Used to calculate the ordered available to promise.",
    )
    previous_promised_qty = fields.Float(
        string="Quantity Promised before this move",
        compute="_compute_previous_promised_qty",
        digits="Product Unit of Measure",
        help="Quantities promised to moves with higher priority than this move "
        "(in default UoM of the product).",
    )
    ordered_available_to_promise_qty = fields.Float(
        string="Ordered Available to Promise (Real Qty)",
        compute="_compute_ordered_available_to_promise",
        digits="Product Unit of Measure",
        help="Available to Promise quantity minus quantities promised "
        " to moves with higher priority (in default UoM of the product).",
    )
    ordered_available_to_promise_uom_qty = fields.Float(
        string="Ordered Available to Promise",
        compute="_compute_ordered_available_to_promise",
        search="_search_ordered_available_to_promise_uom_qty",
        digits="Product Unit of Measure",
        help="Available to Promise quantity minus quantities promised "
        " to moves with higher priority (in initial demand's UoM).",
    )
    release_ready = fields.Boolean(
        compute="_compute_release_ready",
        search="_search_release_ready",
    )
    need_release = fields.Boolean(index=True, copy=False)
    unrelease_allowed = fields.Boolean(compute="_compute_unrelease_allowed")

    @api.depends("rule_id", "rule_id.available_to_promise_defer_pull")
    def _compute_unrelease_allowed(self):
        for move in self:
            unrelease_allowed = move._is_unreleaseable()
            if unrelease_allowed:
                iterator = move._get_chained_moves_iterator("move_orig_ids")
                next(iterator)  # skip the current move
                for origin_moves in iterator:
                    unrelease_allowed = move._is_unrelease_allowed_on_origin_moves(
                        origin_moves
                    )
                    if not unrelease_allowed:
                        break
            move.unrelease_allowed = unrelease_allowed

    def _is_unreleaseable(self):
        """Check if the move can be unrelease. At this stage we only check if
        the move is at the end of a chain of moves and has the caracteristics
        to be unrelease. We don't check the conditions on the origin moves.
        The conditions on the origin moves are checked in the method
        _is_unrelease_allowed_on_origin_moves.
        """
        self.ensure_one()
        user_is_allowed = self.env.user.has_group("stock.group_stock_user")
        return (
            user_is_allowed
            and not self.need_release
            and self.state not in ("done", "cancel")
            and self.picking_type_id.code == "outgoing"
            and self.rule_id.available_to_promise_defer_pull
        )

    def _is_unrelease_allowed_on_origin_moves(self, origin_moves):
        """We check that the origin moves are in a state that allows the unrelease
        of the current move. At this stage, a move can't be unreleased if
          * a picking is already printed. (The work on the picking is planed and
            we don't want to change it)
          * the processing of the origin moves is partially started.
        """
        self.ensure_one()
        pickings = origin_moves.mapped("picking_id")
        if pickings.filtered("printed"):
            # The picking is printed, we can't unrelease the move
            # because the processing of the origin moves is started.
            return False
        origin_moves = origin_moves.filtered(
            lambda m: m.state not in ("done", "cancel")
        )
        origin_qty_todo = sum(origin_moves.mapped("product_qty"))
        return (
            float_compare(
                self.product_qty,
                origin_qty_todo,
                precision_rounding=self.product_uom.rounding,
            )
            <= 0
        )

    def _check_unrelease_allowed(self):
        for move in self:
            if not move.unrelease_allowed:
                raise UserError(
                    _(
                        "You are not allowed to unrelease this move %(move_name)s.",
                        move_name=move.display_name,
                    )
                )

    def _previous_promised_qty_sql_main_query(self):
        return """
            SELECT move.id,
                   COALESCE(SUM(previous_moves.previous_qty), 0.0)
            FROM stock_move move
            LEFT JOIN LATERAL (
                SELECT
                    m.product_qty
                    AS previous_qty
                FROM stock_move m
                INNER JOIN stock_location loc
                ON loc.id = m.location_id
                LEFT JOIN stock_picking_type p_type
                ON m.picking_type_id = p_type.id
                WHERE
                {lateral_where}
                GROUP BY m.id
            ) previous_moves ON true
            WHERE
            move.id IN %(move_ids)s
            GROUP BY move.id;
        """

    def _previous_promised_qty_sql_lateral_where(self):
        locations = self._ordered_available_to_promise_locations()
        sql = """
                m.id != move.id
                AND m.product_id = move.product_id
                AND p_type.code = 'outgoing'
                AND loc.parent_path LIKE ANY(%(location_paths)s)
                AND (
                    COALESCE(m.need_release, False) = COALESCE(move.need_release, False)
                    AND (
                        m.priority > move.priority
                        OR
                        (
                            m.priority = move.priority
                            AND m.date_priority < move.date_priority
                        )
                        OR (
                            m.priority = move.priority
                            AND m.date_priority = move.date_priority
                            AND m.id < move.id
                        )
                    )
                    OR (
                        move.need_release IS true
                        AND (m.need_release IS false OR m.need_release IS null)
                    )
                )
                AND m.state IN (
                    'waiting', 'confirmed', 'partially_available', 'assigned'
                )
        """
        params = {
            "location_paths": [
                "{}%".format(location.parent_path) for location in locations
            ]
        }
        horizon_date = self._promise_reservation_horizon_date()
        if horizon_date:
            sql += (
                " AND (m.need_release IS true AND m.date <= %(horizon)s "
                "      OR m.need_release IS false)"
            )
            params["horizon"] = horizon_date
        return sql, params

    def _previous_promised_qty_sql(self):
        """Lookup query for product promised qty in the same warehouse.

        Moves to consider are either already released or still be to released
        but not done yet. Each of them should fit the reservation horizon.
        """
        params = {"move_ids": tuple(self.ids)}
        lateral_where, lateral_params = self._previous_promised_qty_sql_lateral_where()
        params.update(lateral_params)
        query = self._previous_promised_qty_sql_main_query().format(
            lateral_where=lateral_where
        )
        return query, params

    @api.depends()
    def _compute_previous_promised_qty(self):
        if not self.ids:
            return
        self.env.flush_all()
        self.env["stock.move.line"].flush_model(["move_id", "reserved_qty"])
        self.env["stock.location"].flush_model(["parent_path"])
        self.previous_promised_qty = 0
        query, params = self._previous_promised_qty_sql()
        self.env.cr.execute(query, params)
        rows = dict(self.env.cr.fetchall())
        for move in self:
            move.previous_promised_qty = rows.get(move.id, 0)

    @api.depends(
        "ordered_available_to_promise_qty",
        "picking_id.move_type",
        "picking_id.move_ids",
        "need_release",
    )
    def _compute_release_ready(self):
        for move in self:
            if not move.need_release:
                move.release_ready = False
                continue
            if move.picking_id._get_shipping_policy() == "one":
                move.release_ready = move.picking_id.release_ready
            else:
                move.release_ready = move.ordered_available_to_promise_uom_qty > 0

    def _search_release_ready(self, operator, value):
        if operator != "=":
            raise UserError(_("Unsupported operator %s") % (operator,))
        moves = self.search([("ordered_available_to_promise_uom_qty", ">", 0)])
        moves = moves.filtered(lambda m: m.release_ready)
        return [("id", "in", moves.ids)]

    def _ordered_available_to_promise_locations(self):
        return self.env["stock.warehouse"].search([]).mapped("view_location_id")

    @api.depends()
    def _compute_ordered_available_to_promise(self):
        moves = self.filtered(
            lambda move: move._should_compute_ordered_available_to_promise()
        )
        (self - moves).update(
            {
                "ordered_available_to_promise_qty": 0.0,
                "ordered_available_to_promise_uom_qty": 0.0,
            }
        )

        locations = moves._ordered_available_to_promise_locations()

        # Compute On-Hand quantity (equivalent of qty_available) for all "view
        # locations" of all the warehouses: we may release as soon as we have
        # the quantity somewhere. Do not use "qty_available" to get a faster
        # computation.
        location_domain = []
        for location in locations:
            location_domain = expression.OR(
                [
                    location_domain,
                    [("location_id.parent_path", "=like", location.parent_path + "%")],
                ]
            )
        domain_quant = expression.AND(
            [[("product_id", "in", moves.product_id.ids)], location_domain]
        )
        location_quants = self.env["stock.quant"].read_group(
            domain_quant, ["product_id", "quantity"], ["product_id"], orderby="id"
        )
        quants_available = {
            item["product_id"][0]: item["quantity"] for item in location_quants
        }
        for move in moves:
            product_uom = move.product_id.uom_id
            previous_promised_qty = move.previous_promised_qty

            rounding = product_uom.rounding
            available_qty = float_round(
                quants_available.get(move.product_id.id, 0.0),
                precision_rounding=rounding,
            )

            real_promised = available_qty - previous_promised_qty
            uom_promised = product_uom._compute_quantity(
                real_promised,
                move.product_uom,
                rounding_method="HALF-UP",
            )

            move.ordered_available_to_promise_uom_qty = max(
                min(uom_promised, move.product_uom_qty),
                0.0,
            )
            move.ordered_available_to_promise_qty = max(
                min(real_promised, move.product_qty),
                0.0,
            )

    def _search_ordered_available_to_promise_uom_qty(self, operator, value):
        operator_mapping = {
            "<": py_operator.lt,
            "<=": py_operator.le,
            ">": py_operator.gt,
            ">=": py_operator.ge,
            "=": py_operator.eq,
            "!=": py_operator.ne,
        }
        if operator not in operator_mapping:
            raise UserError(_("Unsupported operator %s") % (operator,))
        moves = self.search([("need_release", "=", True)])
        operator_func = operator_mapping[operator]
        moves = moves.filtered(
            lambda m: operator_func(m.ordered_available_to_promise_uom_qty, value)
        )
        return [("id", "in", moves.ids)]

    def _should_compute_ordered_available_to_promise(self):
        return (
            self.picking_code == "outgoing"
            and not self.product_id.type == "consu"
            and not self.location_id.should_bypass_reservation()
        )

    def _action_cancel(self):
        # Unrelease moves that can be, before canceling them.
        moves_to_unrelease = self.filtered(lambda m: m.unrelease_allowed)
        moves_to_unrelease.unrelease()
        super()._action_cancel()
        self.write({"need_release": False})
        return True

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
            if move.state not in ("confirmed", "waiting", "done", "cancel"):
                continue
            available_quantity = move.ordered_available_to_promise_qty
            if float_compare(available_quantity, 0, precision_digits=precision) <= 0:
                continue

            quantity = min(move.product_qty, available_quantity)
            remaining = move.product_qty - quantity

            if float_compare(remaining, 0, precision_digits=precision) > 0:
                if move.picking_id._get_shipping_policy() == "one":
                    # we don't want to deliver unless we can deliver all at
                    # once
                    continue
                new_move = move._release_split(remaining)
                backorder_links[new_move.picking_id] = move.picking_id

            move._before_release()

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
        unreleased_moves = released_pickings.move_ids - pulled_moves
        for unreleased_move in unreleased_moves:
            if unreleased_move.state in ("done", "cancel"):
                continue
            # no split will occur as we keep the same qty, but the move
            # will be assigned to a new stock.picking
            original_picking = unreleased_move.picking_id
            unreleased_move._release_split(unreleased_move.product_qty)
            backorder_links[unreleased_move.picking_id] = original_picking

        for backorder, origin in backorder_links.items():
            if backorder != origin:
                backorder._release_link_backorder(origin)

        self.env["procurement.group"].run_defer(procurement_requests)

        pulled_moves._after_release_assign_moves()
        pulled_moves._after_release_update_chain()

        return True

    def _before_release(self):
        """Hook that aims to be overridden."""

    def _after_release_update_chain(self):
        picking_ids = set()
        moves = self
        while moves:
            picking_ids.update(moves.mapped("picking_id").ids)
            moves = moves.mapped("move_orig_ids")
        pickings = self.env["stock.picking"].browse(picking_ids)
        pickings._after_release_update_chain()
        # Set the highest priority on all pickings in the chain
        priorities = pickings.mapped("priority")
        if priorities:
            pickings.write({"priority": max(priorities)})

    def _after_release_assign_moves(self):
        move_ids = []
        for origin_moves in self._get_chained_moves_iterator("move_orig_ids"):
            move_ids += origin_moves.ids
        self.env["stock.move"].browse(move_ids)._action_assign()

    def _release_split(self, remaining_qty):
        """Split move and create a new picking for it.

        By default, when we split a move at release to isolate the remaining qty
        into a new move, we also create a new picking for it so that we can
        release it later as soon as the qty is available.
        This behavior can be changed by setting the flag no_backorder_at_release
        on the stock.route of the move. This will allow to create the backorder
        at the end of the picking process and release the unreleased moves into
        the same picking as long as the picking is not done. By doing so, we
        can also cleanup the backorders of the linked pickings created when
        a released move was not processed (no qty found, or no time to do it for
         example).
        """
        context = self.env.context
        self = self.with_context(release_available_to_promise=True)
        new_move = self  # Work on the current move if split doesn't occur
        new_move_vals = self._split(remaining_qty)
        if new_move_vals:
            new_move = self.create(new_move_vals)
            new_move._action_confirm(merge=False)
        # Picking assignment is needed here because `_split` copies the move
        # thus the `_should_be_assigned` condition is not satisfied
        # and the move is not assigned.
        new_move._assign_picking()
        return new_move.with_context(**context)

    def _assign_picking_post_process(self, new=False):
        res = super()._assign_picking_post_process(new)
        priorities = self.mapped("move_dest_ids.picking_id.priority")
        if priorities:
            self.picking_id.write({"priority": max(priorities)})
        return res

    def _get_chained_moves_iterator(self, chain_field):
        """Return an iterator on the moves of the chain.

        The iterator returns the moves in the order of the chain.
        The loop into the iterator is the current moves.
        """
        moves = self
        while moves:
            yield moves
            moves = moves.mapped(chain_field)

    def unrelease(self, safe_unrelease=False):
        """Unrelease unreleasavbe moves

        If safe_unrelease is True, the unreleasaable moves for which the
        processing has already started will be ignored
        """
        moves_to_unrelease = self.filtered(lambda m: m._is_unreleaseable())
        if safe_unrelease:
            moves_to_unrelease = self.filtered("unrelease_allowed")
        moves_to_unrelease._check_unrelease_allowed()
        moves_to_unrelease.write({"need_release": True})
        impacted_picking_ids = set()

        for move in moves_to_unrelease:
            iterator = move._get_chained_moves_iterator("move_orig_ids")
            moves_to_cancel = self.env["stock.move"]
            next(iterator)  # skip the current move
            for origin_moves in iterator:
                origin_moves = origin_moves.filtered(
                    lambda m: m.state not in ("done", "cancel")
                )
                if origin_moves:
                    origin_moves = move._split_origins(origin_moves)
                    impacted_picking_ids.update(origin_moves.mapped("picking_id").ids)
                    # avoid to propagate cancel to the original move
                    origin_moves.write({"propagate_cancel": False})
                    # origin_moves._action_cancel()
                    moves_to_cancel |= origin_moves
            moves_to_cancel._action_cancel()
        moves_to_unrelease.write({"need_release": True})
        for picking, moves in itertools.groupby(
            moves_to_unrelease, lambda m: m.picking_id
        ):
            move_names = "\n".join([m.display_name for m in moves])
            body = _(
                "The following moves have been un-released: \n%(move_names)s",
                move_names=move_names,
            )
            picking.message_post(body=body)

    def _split_origins(self, origins):
        """Split the origins of the move according to the quantity into the
        move and the quantity in the origin moves.

        Return the origins for the move's quantity.
        """
        self.ensure_one()
        qty = self.product_qty
        rounding = self.product_uom.rounding
        new_origin_moves = self.env["stock.move"]
        while float_compare(qty, 0, precision_rounding=rounding) > 0 and origins:
            origin = fields.first(origins)
            if float_compare(qty, origin.product_qty, precision_rounding=rounding) >= 0:
                qty -= origin.product_qty
                new_origin_moves |= origin
            else:
                new_move_vals = origin._split(qty)
                new_origin_moves |= self.create(new_move_vals)
                break
            origins -= origin
        return new_origin_moves

    def _search_picking_for_assignation_domain(self):
        domain = super()._search_picking_for_assignation_domain()
        if self.env.context.get("release_available_to_promise"):
            force_new_picking = not self.rule_id.no_backorder_at_release
            if force_new_picking:
                domain = expression.AND([domain, [("id", "!=", self.picking_id.id)]])
        if self.picking_type_id.prevent_new_move_after_release:
            domain = expression.AND([domain, [("last_release_date", "=", False)]])
        return domain
