# Copyright 2022 Camptocamp SA
# Copyright 2023 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


import pytz

from odoo import fields
from odoo.tools import float_compare

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class Reception(Component):
    """
    Methods for the Reception Process

    You can find a sequence diagram describing states and endpoints relationships
    [here](../docs/reception_sequence_graph.png)
    Keep [the sequence diagram](../docs/reception_sequence_graph.mermaid)
    up-to-date if you change endpoints.

    Process a receipt transfer and track progress by product.

    Once a transfer is selected, you need to:
        1. Select a product (you can scan its barcode or one of its packaging barcodes).
        2. Set the processed quantity.
        3. Put it in an internal PACK (this is optional but can be made mandatory by menu
            configuration). this PACK can be a new one (like an empty pallet) or an existing
            one you add products to (like a pallet you continue to fill in).
        4. Set the location where you put the product (iow. the location where
            is the transport trolley or pallet), unless you fill an existing PACK as its
            location was already defined when its first product was put on it.

    In case of product tracked by lot, you will have to enter the lot number and its
    expiry date (unless it is already known by the system).

    Moves are not validated as they are processed. It is the responsibility of the
    user to decide when to mark as done already processed lines.
    Any remaining lines will be pushed to a backorder.
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.reception"
    _usage = "reception"
    _description = __doc__

    def _check_picking_status(self, pickings):
        # When returns are allowed,
        # the created picking might be empty and cannot be assigned.
        states = ["assigned"]
        if self.work.menu.allow_return:
            states.append("draft")
        return super()._check_picking_status(pickings, states=states)

    def _move_line_by_product(self, product):
        return self.env["stock.move.line"].search(
            self._domain_move_line_by_product(product)
        )

    def _move_line_by_packaging(self, packaging):
        return self.env["stock.move.line"].search(
            self._domain_move_line_by_packaging(packaging)
        )

    def _move_line_by_lot(self, lot):
        return self.env["stock.move.line"].search(self._domain_move_line_by_lot(lot))

    def _scheduled_date_today_domain(self):
        domain = []
        today_start, today_end = self._get_today_start_end_datetime()
        domain.append(("scheduled_date", ">=", today_start))
        domain.append(("scheduled_date", "<=", today_end))
        return domain

    def _get_today_start_end_datetime(self):
        company = self.env.company
        tz = company.partner_id.tz or "UTC"
        today = fields.Datetime.today()
        today_start = fields.Datetime.start_of(today, "day")
        today_end = fields.Datetime.end_of(today, "day")
        today_start_localized = (
            pytz.timezone(tz).localize(today_start).astimezone(pytz.utc)
        )
        today_end_localized = pytz.timezone(tz).localize(today_end).astimezone(pytz.utc)
        return (today_start_localized, today_end_localized)

    # DOMAIN METHODS

    def _domain_move_line_by_packaging(self, packaging):
        return [
            ("move_id.picking_id.picking_type_id", "in", self.picking_types.ids),
            ("move_id.picking_id.state", "=", "assigned"),
            ("move_id.picking_id.user_id", "in", [False, self.env.uid]),
            ("package_id.product_packaging_id", "=", packaging.id),
        ]

    def _domain_move_line_by_product(self, product):
        return [
            ("move_id.picking_id.picking_type_id", "in", self.picking_types.ids),
            ("move_id.picking_id.state", "=", "assigned"),
            ("move_id.picking_id.user_id", "in", [False, self.env.uid]),
            ("product_id", "=", product.id),
        ]

    def _domain_move_line_by_lot(self, lot):
        return [
            ("move_id.picking_id.picking_type_id", "in", self.picking_types.ids),
            ("move_id.picking_id.state", "=", "assigned"),
            ("move_id.picking_id.user_id", "=", False),
            "|",
            ("lot_id.name", "=", lot),
            ("lot_name", "=", lot),
        ]

    def _domain_stock_picking(self, today_only=False):
        domain = [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]
        if today_only:
            domain.extend(self._scheduled_date_today_domain())
        return domain

    def _select_picking(self, picking):
        if picking.picking_type_id not in self.picking_types:
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if picking.state != "assigned":
            return self._response_for_select_document(
                message=self.msg_store.stock_picking_not_available(picking)
            )
        return self._response_for_select_move(picking)

    def _response_for_select_move(self, picking, message=None):
        data = {"picking": self._data_for_stock_picking(picking, with_lines=True)}
        return self._response(next_state="select_move", data=data, message=message)

    def _response_for_confirm_done(self, picking, message=None):
        data = {"picking": self._data_for_stock_picking(picking, with_lines=True)}
        return self._response(next_state="confirm_done", data=data, message=message)

    def _response_for_confirm_new_package(
        self, picking, line, new_package_name, message=None
    ):
        data = {
            "selected_move_line": self._data_for_move_lines(line),
            "picking": self._data_for_stock_picking(picking, with_lines=True),
            "new_package_name": new_package_name,
        }
        return self._response(
            next_state="confirm_new_package", data=data, message=message
        )

    def _select_document_from_move_lines(self, move_lines, msg_func):
        pickings = move_lines.move_id.picking_id
        if len(pickings) == 1:
            if (
                move_lines.product_id.tracking not in ("lot", "serial")
                or move_lines.lot_id
                or move_lines.lot_name
            ):
                return self._response_for_set_quantity(pickings, move_lines)
            return self._response_for_set_lot(pickings, move_lines)
        elif len(pickings) > 1:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        # If no available picking with the right state has been found,
        # return an error
        return self._response_for_select_document(message=msg_func())

    def _scan_document__create_return(self, picking, return_type, barcode):
        stock = self._actions_for("stock")
        return_picking = stock.create_return_picking(picking, return_type, barcode)
        return_picking.action_confirm()
        return return_picking

    def _select_document_from_product(self, product):
        """Select the document by product

        next states:
            - set_lot: a single picking has been found for this packaging
            - select_document: A single or no pickings has been found for this packaging
        """
        move_lines = self._move_line_by_product(product).filtered(
            lambda l: l.picking_id.picking_type_id.id in self.picking_types.ids
        )
        pickings = move_lines.move_id.picking_id
        if pickings:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        return self._response_for_select_document(
            pickings=pickings,
            message=self.msg_store.product_not_found_in_pickings(),
        )

    def _select_document_from_packaging(self, packaging):
        """Select the document by packaging

        next states:
            - set_lot: a single picking has been found for this packaging
            - select_document: A single or no pickings has been found for this packaging
        """
        move_lines = self._move_line_by_packaging(packaging).filtered(
            lambda l: l.picking_id.picking_type_id.id in self.picking_types.ids
        )
        pickings = move_lines.move_id.picking_id
        if pickings:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        return self._response_for_select_document(
            pickings=pickings,
            message=self.msg_store.product_not_found_in_pickings(),
        )

    def _select_document_from_lot(self, lot):
        """Select the document by lot

        next states:
            - set_lot: a single picking has been found for this packaging
            - select_document: A single or no pickings has been found for this packaging
        """
        move_lines = self._move_line_by_lot(lot)
        if not move_lines:
            return
        pickings = move_lines.move_id.picking_id
        if pickings:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        return self._response_for_select_document(
            pickings=pickings,
            message=self.msg_store.lot_not_found_in_pickings(),
        )

    def _scan_line__find_or_create_line(self, picking, move, qty_done=1):
        """Find or create a line  on a move for the user to work on.

        First try to find a line already assigned to the user.
        Then a line that is not yet assigned to any users (locking the line
        to avoid concurent access.)
        If none are found create a new line.

        """
        line = None
        unassigned_lines = self.env["stock.move.line"]
        for move_line in move.move_line_ids:
            if move_line.result_package_id:
                continue
            if move_line.shopfloor_user_id.id == self.env.uid:
                line = move_line
                break
            elif not move_line.shopfloor_user_id:
                unassigned_lines |= move_line
        if not line and unassigned_lines:
            lock = self._actions_for("lock")
            for move_line in unassigned_lines:
                if lock.for_update(move_line, skip_locked=True):
                    line = move_line
                    break
        if not line:
            values = move._prepare_move_line_vals()
            line = self.env["stock.move.line"].create(values)
        return self._scan_line__assign_user(picking, line, qty_done)

    def _scan_line__assign_user(self, picking, line, qty_done):
        product = line.product_id
        self._assign_user_to_line(line)
        line.qty_done += qty_done
        if product.tracking not in ("lot", "serial") or (line.lot_id or line.lot_name):
            return self._before_state__set_quantity(picking, line)
        return self._response_for_set_lot(picking, line)

    def _select_line__filter_lines_by_packaging__return(self, lines, packaging):
        return_line = fields.first(
            lines.filtered(
                lambda l: not l.package_id.product_packaging_id
                and not l.result_package_id
                and l.shopfloor_user_id.id in (False, self.env.uid)
            )
        )
        if return_line:
            return return_line

    def _select_line__filter_lines_by_packaging(self, lines, packaging):
        if self.work.menu.allow_return:
            line = self._select_line__filter_lines_by_packaging__return(
                lines, packaging
            )
            if line:
                return line
        return fields.first(
            lines.filtered(
                lambda l: l.package_id.product_packaging_id == packaging
                and not l.result_package_id
                and l.shopfloor_user_id.id in [False, self.env.uid]
            )
        )

    def _order_stock_picking(self):
        # We sort by scheduled date first. However, there might be a case
        # where two pickings have the exact same scheduled date.
        # In that case, we sort by id.
        return "scheduled_date ASC, id ASC"

    def _scan_document__by_picking(self, pickings, barcode):
        picking_filter_result = pickings
        reception_pickings = picking_filter_result.filtered(
            lambda p: p.picking_type_id.id in self.picking_types.ids
        )
        if (
            picking_filter_result
            and not reception_pickings
            and not self.work.menu.allow_return
        ):
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if reception_pickings:
            message = self._check_picking_status(reception_pickings)
            if message:
                return self._response_for_select_document(
                    pickings=reception_pickings, message=message
                )
            # There is a case where scanning the source document
            # could return more than one picking.
            # If there's only one picking due today, we go to the next screen.
            # Otherwise, we ask the user to scan a package instead.
            today_start, today_end = self._get_today_start_end_datetime()
            picking_filter_result_due_today = picking_filter_result.filtered(
                lambda p: today_start
                <= p.scheduled_date.astimezone(pytz.utc)
                < today_end
            )
            if len(picking_filter_result_due_today) == 1:
                return self._select_picking(picking_filter_result_due_today)
            if len(picking_filter_result) > 1:
                return self._response_for_select_document(
                    pickings=reception_pickings,
                    message=self.msg_store.source_document_multiple_pickings_scan_package(),
                )
            return self._select_picking(reception_pickings)

    def _scan_document__by_product(self, product, barcode):
        if product:
            return self._select_document_from_product(product)

    def _scan_document__by_packaging(self, packaging, barcode):
        if packaging:
            return self._select_document_from_packaging(packaging)

    def _scan_document__by_lot(self, lot, barcode):
        if lot:
            return self._select_document_from_lot(lot)

    def _scan_document__by_origin_move(self, moves, barcode):
        if not self.work.menu.allow_return:
            # A return picking has been scanned, but allow rma is disabled.
            return self._scan_document__fallback()
        pickings = moves.picking_id
        outgoing_pickings = pickings.filtered(
            lambda p: (p.picking_type_code == "outgoing")
        )
        # If we find valid pickings for a return, then we create an empty
        # return picking
        if outgoing_pickings:
            # But first, check that return types are correctly set up,
            # as we cannot create a return move with empty locations.
            return_types = self.picking_types.filtered(
                lambda t: t.default_location_src_id and t.default_location_dest_id
            )
            if not return_types:
                message = self.msg_store.no_default_location_on_picking_type()
                return self._response_for_select_document(message=message)
            return_picking = self._scan_document__create_return(
                fields.first(outgoing_pickings), fields.first(return_types), barcode
            )
            return self._response_for_select_move(return_picking)

    def _scan_document__fallback(self):
        return self._response_for_select_document(
            message=self.msg_store.barcode_not_found()
        )

    def _scan_line__create_return_move(self, return_picking, origin_moves):
        # copied from odoo/src/addons/stock/wizard/stock_picking_return.py
        stock = self._actions_for("stock")
        return stock.create_return_move(return_picking, origin_moves)

    def _scan_line__by_product__return(self, picking, product):
        search = self._actions_for("search")
        origin_move_domain = [
            ("picking_id.picking_type_code", "=", "outgoing"),
        ]
        origin_moves = search.origin_move_from_scan(
            picking.origin, extra_domain=origin_move_domain
        )
        origin_moves_for_product = origin_moves.filtered(
            lambda m: m.product_id == product
        )
        # If we have an origin picking but no origin move, then user
        # scanned a wrong product. Warn him about this.
        if origin_moves and not origin_moves_for_product:
            message = self.msg_store.product_not_found_in_current_picking()
            return self._response_for_select_move(picking, message=message)
        if origin_moves_for_product:
            return_move = self._scan_line__create_return_move(
                picking, origin_moves_for_product
            )
            if not return_move:
                # It means that among all origin moves, none has been found with
                # max qty to return being positive.
                # Which means all lines have already been returned.
                message = self.msg_store.move_already_returned()
                return self._response_for_select_move(picking, message=message)
            picking.action_confirm()
            picking.action_assign()
            return self._scan_line__find_or_create_line(picking, return_move)

    def _scan_line__by_product(self, picking, product):
        moves = picking.move_lines.filtered(lambda m: m.product_id == product)
        # Only create a return if don't already have a maching reception move
        if not moves and self.work.menu.allow_return:
            response = self._scan_line__by_product__return(picking, product)
            if response:
                return response
        # Otherwise, the picking isn't a return, and should be a regular reception
        message = not moves and self._check_move_available(moves, "product")
        for move in moves:
            message = self._check_move_available(move, "product")
            if not message:
                return self._scan_line__find_or_create_line(picking, move)
        return self._response_for_select_move(
            picking,
            message=message,
        )

    def _scan_line__by_packaging__return(self, picking, packaging):
        search = self._actions_for("search")
        origin_move_domain = [
            ("picking_id.picking_type_code", "=", "outgoing"),
        ]
        origin_moves = search.origin_move_from_scan(
            picking.origin, extra_domain=origin_move_domain
        )
        origin_moves_for_packaging = origin_moves.filtered(
            lambda m: packaging in m.product_id.packaging_ids
        )
        if origin_moves and not origin_moves_for_packaging:
            message = self.msg_store.packaging_not_found_in_picking()
            return self._response_for_select_move(picking, message=message)
        # If we have an origin move, create the return move, and go to next screen
        if origin_moves_for_packaging:
            return_move = self._scan_line__create_return_move(
                picking, origin_moves_for_packaging
            )
            return_move._action_confirm()
            return self._scan_line__find_or_create_line(
                picking, return_move, packaging.qty
            )

    def _scan_line__by_packaging(self, picking, packaging):
        move = picking.move_lines.filtered(
            lambda m: packaging in m.product_id.packaging_ids
        )
        # Only create a return if don't already have a maching reception move
        if not move and self.work.menu.allow_return:
            response = self._scan_line__by_packaging__return(picking, packaging)
            if response:
                return response
        message = self._check_move_available(move, "packaging")
        if message:
            return self._response_for_select_move(
                picking,
                message=message,
            )
        return self._scan_line__find_or_create_line(picking, move)

    def _scan_line__by_lot(self, picking, lot):
        lines = picking.move_line_ids.filtered(
            lambda l: (
                lot == l.lot_id
                or (lot.name == l.lot_name and lot.product_id == l.product_id)
                and not l.result_package_id
            )
        )
        if not lines:
            return self._scan_line__by_product(picking, lot.product_id)
        # TODO probably suboptimal
        # We might have an available line, but it might be the last one.
        # Loop over the recordset and break as soon as we find one.
        for line in lines:
            message = self._check_move_available(line.move_id, message_code="lot")
            if not message:
                break
        if message:
            return self._response_for_select_move(
                picking,
                message=message,
            )
        return self._scan_line__assign_user(picking, line, 1)

    def _scan_line__fallback(self, picking, barcode):
        # We might have lines with no lot, but with a lot_name.
        lines = picking.move_line_ids.filtered(
            lambda l: l.lot_name == barcode and not l.result_package_id
        )
        if not lines:
            return self._response_for_select_move(
                picking, message=self.msg_store.barcode_not_found()
            )
        for line in lines:
            message = self._check_move_available(line.move_id, message_code="lot")
            if not message:
                return self._scan_line__assign_user(picking, line, 1)
        return self._response_for_select_move(
            picking,
            message=message,
        )

    def _check_move_available(self, move, message_code="product"):
        if not move:
            message_code = message_code.capitalize()
            return self.msg_store.x_not_found_or_already_in_dest_package(message_code)
        line_without_package = any(
            not ml.result_package_id for ml in move.move_line_ids
        )
        if move.product_uom_qty - move.quantity_done < 1 and not line_without_package:
            return self.msg_store.move_already_done()

    def _set_quantity__check_quantity_done(self, selected_line):
        move = selected_line.move_id
        max_qty_done = move.product_uom_qty
        qty_done = sum(move.move_line_ids.mapped("qty_done"))
        rounding = selected_line.product_uom_id.rounding
        return float_compare(qty_done, max_qty_done, precision_rounding=rounding)

    def _set_quantity__by_product(self, picking, selected_line, product):
        # This is a general rule here. whether the return has been created from
        # shopfloor or not, you cannot return more than what was shipped.
        # Therefore, we cannot use the `is_shopfloor_created` here.
        previous_vals = {
            "qty_done": selected_line.qty_done,
        }
        is_return_line = bool(selected_line.move_id.origin_returned_move_id)
        if product.id != selected_line.product_id.id:
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.wrong_record(product),
            )
        selected_line.qty_done += 1
        response = self._response_for_set_quantity(picking, selected_line)
        if self.work.menu.allow_return and is_return_line:
            message_type = response.get("message", {}).get("message_type")
            # If we have an error, return it, since this is also true for return lines
            if message_type == "error":
                return response
            compare = self._set_quantity__check_quantity_done(selected_line)
            # We cannot set a qty_done superior to what has initally been sent
            if compare == 1:
                # If so, reset selected_line to its previous state, and return an error
                selected_line.write(previous_vals)
                message = self.msg_store.return_line_invalid_qty()
                return self._response_for_set_quantity(
                    picking, selected_line, message=message
                )
        return response

    def _set_quantity__by_packaging(self, picking, selected_line, packaging):
        # This is a general rule here. whether the return has been created from
        # shopfloor or not, you cannot return more than what was shipped.
        # Therefore, we cannot use the `is_shopfloor_created` here.
        previous_vals = {
            "qty_done": selected_line.qty_done,
        }
        is_return_line = bool(selected_line.move_id.origin_returned_move_id)
        if packaging.product_id.id != selected_line.product_id.id:
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.wrong_record(packaging),
            )
        selected_line.qty_done += packaging.qty
        response = self._response_for_set_quantity(picking, selected_line)
        if self.work.menu.allow_return and is_return_line:
            message_type = response.get("message", {}).get("message_type")
            # If we have an error, return it, since this is also true for return lines
            if message_type == "error":
                return response
            compare = self._set_quantity__check_quantity_done(selected_line)
            # We cannot set a qty_done superior to what has initally been sent
            if compare == 1:
                # If so, reset selected_line to its previous state, and return an error
                selected_line.write(previous_vals)
                message = self.msg_store.return_line_invalid_qty()
                return self._response_for_set_quantity(
                    picking, selected_line, message=message
                )
        return response

    def _set_package_on_move_line(self, picking, line, package):
        """Assign a package already on a move line.

        If the package is already at a location :
            * check the location is valid
            * Split the move if doing a partial quantity

        On error, return to the set quantity screen.

        """
        pack_location = package.location_id
        if not pack_location:
            line.result_package_id = package
            return None
        (
            move_dest_location_ok,
            pick_type_dest_location_ok,
        ) = self._check_location_ok(pack_location, line, picking)
        if not (move_dest_location_ok or pick_type_dest_location_ok):
            # Package location is not a child of the move destination
            message = self.msg_store.dest_location_not_allowed()
            return self._response_for_set_quantity(picking, line, message=message)
        quantity = line.qty_done
        response = self._set_quantity__process__set_qty_and_split(
            picking, line, quantity
        )
        if response:
            return response
        # If the scanned package has a valid destination,
        # set both package and destination on the package.
        line.result_package_id = package
        line.location_dest_id = pack_location

    def _set_quantity__by_package(self, picking, selected_line, package):
        response = self._set_package_on_move_line(picking, selected_line, package)
        if response:
            return response
        if package.location_id:
            response = self._post_line(selected_line)
            if response:
                return response
            return self._response_for_select_move(picking)
        return self._response_for_set_destination(picking, selected_line)

    def _set_quantity__by_location(self, picking, selected_line, location):
        move_dest_location_ok, pick_type_dest_location_ok = self._check_location_ok(
            location, selected_line, picking
        )
        if not (move_dest_location_ok or pick_type_dest_location_ok):
            # Scanned location isn't a child of the move's dest location
            message = self.msg_store.dest_location_not_allowed()
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        # process without pack, set destination location, and go back to
        # `select_move`
        selected_line.location_dest_id = location
        return self._response_for_select_move(picking)

    def _set_quantity__by_lot(self, picking, selected_line, barcode):
        if selected_line.lot_id.name == barcode or selected_line.lot_name == barcode:
            selected_line.qty_done += 1
            return self._response_for_set_quantity(picking, selected_line)

    def _check_location_ok(self, location, selected_line, picking):
        if location.usage == "view":
            return (False, False)

        move_dest_location = selected_line.location_dest_id
        pick_type_dest_location = picking.picking_type_id.default_location_dest_id

        move_dest_location_ok = location.parent_path.startswith(
            move_dest_location.parent_path
        )
        pick_type_dest_location_ok = location.parent_path.startswith(
            pick_type_dest_location.parent_path
        )
        if move_dest_location_ok or pick_type_dest_location_ok:
            return (move_dest_location_ok, pick_type_dest_location_ok)

        return (False, False)

    def _use_handlers(self, handlers, *args, **kwargs):
        for handler in handlers:
            response = handler(*args, **kwargs)
            if response:
                return response

    def _assign_user_to_line(self, line):
        line.shopfloor_user_id = self.env.user

    # DATA METHODS

    def _data_for_stock_picking(self, picking, with_lines=False, **kw):
        if "with_progress" not in kw:
            kw["with_progress"] = True
        data = self.data.picking(picking, **kw)
        if with_lines:
            data.update({"moves": self._data_for_moves(picking.move_lines)})
        return data

    def _data_for_stock_pickings(self, pickings, with_lines=False):
        return [
            self._data_for_stock_picking(picking, with_lines=with_lines)
            for picking in pickings
        ]

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    def _data_for_moves(self, moves, **kw):
        return self.data.moves(moves, **kw)

    # RESPONSES

    def _response_for_select_document(self, pickings=None, message=None):
        if not pickings:
            pickings = self.env["stock.picking"].search(
                self._domain_stock_picking(today_only=True),
                order=self._order_stock_picking(),
            )
        else:
            # We sort by scheduled date first. However, there might be a case
            # where two pickings have the exact same scheduled date.
            # In that case, we sort by id.
            pickings = pickings.sorted(
                lambda p: (p.scheduled_date, p.id), reverse=False
            )
        data = {"pickings": self._data_for_stock_pickings(pickings, with_lines=False)}
        return self._response(next_state="select_document", data=data, message=message)

    def _response_for_manual_selection(self):
        pickings = self.env["stock.picking"].search(
            self._domain_stock_picking(),
            order=self._order_stock_picking(),
        )
        data = {"pickings": self._data_for_stock_pickings(pickings, with_lines=False)}
        return self._response(next_state="manual_selection", data=data)

    def _response_for_set_lot(self, picking, line, message=None):
        return self._response(
            next_state="set_lot",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _align_display_product_uom_qty(self, line, response):
        # This method aligns product uom qties on move lines.
        # In the shopfloor context, we might have multiple users working at
        # the same time on the same move. This is done by creating one move line
        # per user, with shopfloor_user_id = user.
        # This method ensures that the product_uom_qty reflects what remains to
        # be done, so we can display coherent numbers on the UI.

        # for a given line, product_uom_qty is computed as this:
        # remaining_todo = move.product_uom_qty - move.quantity_done
        # line.product_uom_qty = line.qty_done + remaining_todo

        # TODO, do we need to check move's state?
        # If move is already done, do not update lines qties
        # if move.state in ("done", "cancel"):
        #     return
        move = line.move_id
        qty_todo = move.product_uom_qty
        other_lines_qty_done = 0.0
        move_uom = move.product_uom
        for move_line in move.move_line_ids - line:
            # Use move's uom
            line_uom = move_line.product_uom_id
            other_lines_qty_done += line_uom._compute_quantity(
                move_line.qty_done, move_line.product_uom_id, round=False
            )
        remaining_todo = qty_todo - other_lines_qty_done
        # Change back to line uom
        line_todo = line.product_uom_id._compute_quantity(
            remaining_todo, move_uom, round=False
        )
        # If more has been done keep the quantity to zero
        response["data"]["set_quantity"]["selected_move_line"][0]["quantity"] = max(
            line_todo, 0
        )
        return response

    def _before_state__set_quantity(self, picking, line, message=None):
        # Used by inherting module  see shopfloor_reception_packaging_dimension
        return self._response_for_set_quantity(picking, line, message=message)

    def _response_for_set_quantity(
        self, picking, line, message=None, asking_confirmation=None
    ):
        response = self._response(
            next_state="set_quantity",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
                "confirmation_required": asking_confirmation,
            },
            message=message,
        )
        return self._align_display_product_uom_qty(line, response)

    def _response_for_set_destination(self, picking, line, message=None):
        return self._response(
            next_state="set_destination",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _response_for_select_dest_package(self, picking, line, message=None):
        # NOTE: code taken from the checkout scenario.
        # Maybe refactor it to avoid repetitions.
        packages = picking.move_line_ids.result_package_id
        if not packages:
            return self._response_for_set_quantity(
                picking,
                line,
                message=self.msg_store.no_valid_package_to_select(),
            )
        packages_data = self.data.packages(
            packages.with_context(picking_id=picking.id).sorted(),
            picking=picking,
            with_packaging=True,
        )
        return self._response(
            next_state="select_dest_package",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "packages": packages_data,
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    # ENDPOINTS

    def start(self):
        return self._response_for_select_document()

    def _scan_document__get_handlers_by_type(self):
        return {
            "picking": self._scan_document__by_picking,
            # only add the handler if scan_location_or_pack_first is disabled
            "product": (
                self._scan_document__by_product
                if not self.work.menu.scan_location_or_pack_first
                else None
            ),
            "packaging": self._scan_document__by_packaging,
            "lot": self._scan_document__by_lot,
            "origin_move": self._scan_document__by_origin_move,
        }

    def _scan_document__get_find_kw(self):
        return {
            "picking": {"use_origin": True},
            "delivered_picking": {"use_origin": True},
        }

    def scan_document(self, barcode):
        """Scan a picking, a product or a packaging.

        If an outgoing done move's origin is scanned, a return picking will be created.

        Input:
            barcode: the barcode of a product, a packaging, a picking name or a lot

        transitions:
          - select_document: Error: barcode not found
          - select_document: Multiple picking matching the product / packaging barcode
          - select_move: Picking scanned, one has been found
          - manual_selection: Press 'manual select' button, all available pickings are displayed
          - set_lot: Packaging / Product has been scanned,
                        single correspondance. Tracked product
          - set_quantity: Packaging / Product has been scanned,
                        single correspondance. Not tracked product
        """
        handlers_by_type = self._scan_document__get_handlers_by_type()
        search = self._actions_for("search")
        find_kw = self._scan_document__get_find_kw()
        for handler_type, handler in handlers_by_type.items():
            record = search._find_record_by_type(
                barcode, handler_type, handler_kw=find_kw
            )
            if not record:
                continue
            res = handler(record, barcode)
            if res:
                return res
        return self._scan_document__fallback()

    def list_stock_pickings(self):
        """Select a picking manually

        transitions:
        - select_document: Press 'back' button
        - select_move: Picking selected
        - set_lot: Picking selected, single correspondance. Tracked product
        - set_quantity: Picking selected, single correspondance. Not tracked product

        This endpoint returns the list of all pickings available
        so that the user can select one manually

        Since there's no scan in the manual_selection screen
        there are only two options:
            - Select an available picking and move to the next screen
            - Go back to select_document

        This means there should be no room for error
        """
        return self._response_for_manual_selection()

    def scan_line(self, picking_id, barcode):
        """Scan a product or a packaging

        input:
            barcode: The barcode of a product, a packaging or a lot

        transitions:
          - select_move: Error: barcode not found
          - set_lot: Packaging / Product has been scanned. Tracked product
          - set_quantity: Packaging / Product has been scanned. Not tracked product
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_move(picking, message=message)
        handlers_by_type = {
            "product": self._scan_line__by_product,
            "packaging": self._scan_line__by_packaging,
            "lot": self._scan_line__by_lot,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, handlers_by_type.keys())
        # Fallback handler, returns a barcode not found error
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(picking, search_result.record)
        return self._scan_line__fallback(picking, barcode)

    def manual_select_move(self, move_id):
        move = self.env["stock.move"].browse(move_id)
        picking = move.picking_id
        return self._scan_line__find_or_create_line(picking, move)

    def done_action(self, picking_id, confirmation=False):
        """Mark a picking as done

        input:
            confirmation: if false, ask for confirmation; if true, mark as done

        transitions:
          - select_move: Error: no qty done
          - select_move: Error: picking not found
          - confirm_done: Ask for confirmation
          - select_document: Mark as done
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_move(picking, message=message)
        if all(line.qty_done == 0 for line in picking.move_line_ids):
            # If no line has been processed, refuse to set the picking as done
            return self._response_for_select_move(
                picking, message=self.msg_store.transfer_no_qty_done()
            )
        cancel_backorder = picking.is_shopfloor_created and self.work.menu.allow_return
        if not confirmation and not cancel_backorder:
            to_backorder = picking._check_backorder()
            if to_backorder:
                # Not all lines are fully done, ask the user to confirm the
                # backorder creation
                return self._response_for_confirm_done(
                    picking, message=self.msg_store.transfer_confirm_done()
                )
            # all lines are done, ask the user to confirm anyway
            return self._response_for_confirm_done(
                picking, message=self.msg_store.need_confirmation()
            )
        self._handle_backorder(picking, cancel_backorder)
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(picking)
        )

    def _handle_backorder(self, picking, cancel_backorder=False):
        """This method handles backorders that could be created at picking confirm."""
        if cancel_backorder:
            picking = picking.with_context(cancel_backorder=True)
        backorders_before = picking.backorder_ids
        picking._action_done()
        if not cancel_backorder:
            backorders_after = picking.backorder_ids - backorders_before
            # Remove user_id on backorder, if any
            backorders_after.user_id = False

    def set_lot(
        self, picking_id, selected_line_id, lot_name=None, expiration_date=None
    ):
        """Set lot and its expiration date

        Input:
            barcode: The barcode of a lot
            expiration_date: The expiration_date

        transitions:
          - select_move: User clicked on back
          - set_lot: Barcode not found. Ask user to create one from barcode
          - set_lot: expiration_date has been set on the selected line
          - set_lot: lot_it has been set on the selected line
          - set_lot: Error: expiration_date is required
          - set_quantity: User clicked on the confirm button
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_lot(picking, selected_line, message=message)
        if not selected_line.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_lot(picking, selected_line, message=message)
        search = self._actions_for("search")
        if lot_name:
            product = selected_line.product_id
            lot = search.lot_from_scan(lot_name, products=product)
            if not lot:
                lot = self.env["stock.production.lot"].create(
                    self._create_lot_values(product, lot_name)
                )
            selected_line.lot_id = lot.id
            selected_line._onchange_lot_id()
        elif expiration_date:
            selected_line.write({"expiration_date": expiration_date})
            selected_line.lot_id.write({"expiration_date": expiration_date})
        return self._response_for_set_lot(picking, selected_line)

    def _create_lot_values(self, product, lot_name):
        return {
            "name": lot_name,
            "product_id": product.id,
            "company_id": self.env.company.id,
            "use_expiration_date": product.use_expiration_date,
        }

    def set_lot_confirm_action(self, picking_id, selected_line_id):
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        if message:
            return self._response_for_set_lot(picking, selected_line, message=message)
        message = self._check_expiry_date(selected_line)
        if message:
            return self._response_for_set_lot(picking, selected_line, message=message)
        return self._before_state__set_quantity(picking, selected_line)

    def _check_expiry_date(self, line):
        use_expiration_date = (
            line.product_id.use_expiration_date or line.lot_id.use_expiration_date
        )
        if use_expiration_date and not line.expiration_date:
            return self.msg_store.expiration_date_missing()

    def _set_quantity__get_handlers_by_type(self):
        return {
            "product": self._set_quantity__by_product,
            "packaging": self._set_quantity__by_packaging,
            "package": self._set_quantity__by_package,
            "location": self._set_quantity__by_location,
            "lot": self._set_quantity__by_lot,
        }

    def _set_quantity__by_barcode(
        self, picking, selected_line, barcode, confirmation=None
    ):
        handlers_by_type = self._set_quantity__get_handlers_by_type()
        search = self._actions_for("search")
        search_result = search.find(barcode, handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(picking, selected_line, search_result.record)
        # Nothing found, ask user if we should create a new pack for the scanned
        # barcode
        if confirmation != barcode:
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.create_new_pack_ask_confirmation(barcode),
                asking_confirmation=barcode,
            )
        package = self.env["stock.quant.package"].create({"name": barcode})
        selected_line.result_package_id = package
        return self._response_for_set_destination(picking, selected_line)

    def _set_quantity__assign_quantity(self, picking, selected_line, quantity):
        # If this is a return line, we cannot assign more qty_done than what
        # was originally sent.
        is_return_line = bool(selected_line.move_id.origin_returned_move_id)
        max_qty_done = selected_line.move_id.product_uom_qty
        if is_return_line and self.work.menu.allow_return:
            if quantity > max_qty_done:
                message = self.msg_store.return_line_invalid_qty()
                return self._response_for_set_quantity(
                    picking, selected_line, message=message
                )
        selected_line.qty_done = quantity

    def set_quantity(
        self,
        picking_id,
        selected_line_id,
        quantity=None,
        barcode=None,
        confirmation=None,
    ):
        """Set the quantity done

        Input:
            quantity: the quantity to set
            barcode: Barcode of a product / packaging to determine the qty to increment
            barcode: Barcode of a package / location to set on the line

        transitions:
          - select_move: User clicked on back
          - set_lot: Barcode not found. Ask user to create one from barcode
          - set_lot: expiration_date has been set on the selected line
          - set_lot: lot_it has been set on the selected line
          - set_lot: Error: expiration_date is required
          - set_quantity: User clicked on the confirm button
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        if not selected_line.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        if quantity is not None:
            # We set qty_done to be equal to the qty of the picker
            # at the moment of the scan.
            response = self._set_quantity__assign_quantity(
                picking, selected_line, quantity
            )
            if response:
                return response
        if barcode:
            # Then, we add the qty of whatever was scanned
            # on top of the qty of the picker.
            return self._set_quantity__by_barcode(
                picking, selected_line, barcode, confirmation
            )
        return self._response_for_set_quantity(picking, selected_line)

    def set_quantity__cancel_action(self, picking_id, selected_line_id):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        if selected_line.exists():
            if selected_line.product_uom_qty:
                stock = self._actions_for("stock")
                stock.unmark_move_line_as_picked(selected_line)
            else:
                selected_line.unlink()
        return self._response_for_select_move(picking)

    def _set_quantity__process__set_qty_and_split(self, picking, line, quantity):
        move = line.move_id
        sum(move.move_line_ids.mapped("qty_done"))
        savepoint = self._actions_for("savepoint").new()
        line.qty_done = quantity
        compare = self._set_quantity__check_quantity_done(line)
        if compare == 1:
            # If move's qty_done > to move's qty_todo, rollback and return an error
            savepoint.rollback()
            return self._response_for_set_quantity(
                picking, line, message=self.msg_store.unable_to_pick_qty()
            )
        savepoint.release()
        # Only if total_qty_done < qty_todo, we split the move line
        if compare == -1:
            default_values = {
                "lot_id": False,
                "shopfloor_user_id": False,
                "expiration_date": False,
            }
            line._split_qty_to_be_done(quantity, **default_values)

    def process_with_existing_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        response = self._set_quantity__process__set_qty_and_split(
            picking, selected_line, quantity
        )
        if response:
            return response
        return self._response_for_select_dest_package(picking, selected_line)

    def process_with_new_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        response = self._set_quantity__process__set_qty_and_split(
            picking, selected_line, quantity
        )
        if response:
            return response
        picking._put_in_pack(selected_line)
        return self._response_for_set_destination(picking, selected_line)

    def process_without_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        response = self._set_quantity__process__set_qty_and_split(
            picking, selected_line, quantity
        )
        if response:
            return response
        return self._response_for_set_destination(picking, selected_line)

    def _post_line(self, selected_line):
        selected_line.product_uom_qty = selected_line.qty_done
        if (
            selected_line.picking_id.is_shopfloor_created
            and self.work.menu.allow_return
        ):
            # If the transfer is not planned, and we allow unplanned returns,
            # process the returned qty and mark it as done.
            return self._post_shopfloor_created_line(selected_line)

        if self.work.menu.auto_post_line:
            # If option auto_post_line is active in the shopfloor menu,
            # create a split order with this line.
            self._auto_post_line(selected_line)

    def _post_shopfloor_created_line(self, selected_line):
        selected_line.product_uom_qty = selected_line.qty_done
        selected_line.picking_id.with_context(cancel_backorder=True)._action_done()
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(selected_line.picking_id)
        )

    def _auto_post_line(self, selected_line):
        # If user only processed 1/5 and is the only one working on the move,
        # then selected_line is the only one related to this move.
        # In such case, we must ensure there's another move with the remaining
        # quantity to do, so selected_line is extracted in a new move as expected.

        # Always keep the quantity todo at zero, the same is done
        # in Odoo when move lines are created manually (setting)
        lines_with_qty_todo = selected_line.move_id.move_line_ids.filtered(
            lambda line: line.state not in ("cancel", "done")
            and line.product_uom_qty > 0
        )
        move = selected_line.move_id
        lock = self._actions_for("lock")
        lock.for_update(move)
        if lines_with_qty_todo:
            lines_with_qty_todo.product_uom_qty = 0

        move_quantity = move.product_uom._compute_quantity(
            move.product_uom_qty, selected_line.product_uom_id
        )
        if selected_line.qty_done == move_quantity:
            # In case of full quantity, post the initial move
            return selected_line.move_id.extract_and_action_done()
        split_move_vals = move._split(selected_line.qty_done)
        new_move = move.create(split_move_vals)
        new_move.move_line_ids = selected_line
        new_move._action_confirm(merge=False)
        new_move._recompute_state()
        new_move._action_assign()
        # Set back the quantity to do on one of the lines
        line = fields.first(
            move.move_line_ids.filtered(
                lambda line: line.state not in ("cancel", "done")
            )
        )
        if line:
            move_quantity = move.product_uom._compute_quantity(
                move.product_uom_qty, line[0].product_uom_id
            )
            line.product_uom_qty = move_quantity
        move._recompute_state()
        new_move.extract_and_action_done()

    def set_destination(
        self, picking_id, selected_line_id, location_name, confirmation=False
    ):
        """Set the destination on the move line.

        input:
            location_name: The name of the location

        transitions:
          - set_destination: Warning: User scanned a child location of the picking type.
            Ask for confirmation
          - set_destination: Error: User tried to scan a non-valid location
          - select_move: User scanned a child location of the move's dest location
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_destination(
                picking, selected_line, message=message
            )
        if not selected_line.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_destination(
                picking, selected_line, message=message
            )
        search = self._actions_for("search")

        location = search.location_from_scan(location_name)
        if not location:
            return self._response_for_set_destination(
                picking, selected_line, message=self.msg_store.no_location_found()
            )
        move_dest_location_ok, pick_type_dest_location_ok = self._check_location_ok(
            location, selected_line, picking
        )
        if not (move_dest_location_ok or pick_type_dest_location_ok):
            return self._response_for_set_destination(
                picking,
                selected_line,
                message=self.msg_store.dest_location_not_allowed(),
            )
        if move_dest_location_ok:
            # If location is a child of move's dest location, assign it without asking
            selected_line.location_dest_id = location
        elif pick_type_dest_location_ok:
            # If location is a child of picking types's dest location,
            # ask for confirmation before assigning
            if not confirmation:
                return self._response_for_set_destination(
                    picking,
                    selected_line,
                    message=self.msg_store.place_in_location_ask_confirmation(
                        location.name
                    ),
                )
            selected_line.location_dest_id = location
        response = self._post_line(selected_line)
        if response:
            return response
        return self._response_for_select_move(picking)

    def select_dest_package(
        self, picking_id, selected_line_id, barcode, confirmation=False
    ):
        """Select the destination package for the move line

        Input:
            barcode: The barcode of the package

        transitions:
          - select_move: User scanned a valid package
          - select_dest_package: Warning: User scanned an unknown barcode.
            Confirm to create one.
          - select_dest_package: Error: User scanned a non-empty package
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_dest_package(
                picking, selected_line, message=message
            )
        if not selected_line.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_select_dest_package(
                picking, selected_line, message=message
            )
        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if not package and confirmation:
            package = self.env["stock.quant.package"].create({"name": barcode})
        if package:
            # Do not allow user to create a non-empty package
            if package.quant_ids:
                return self._response_for_select_dest_package(
                    picking,
                    selected_line,
                    message=self.msg_store.package_not_empty(package),
                )
            response = self._set_package_on_move_line(picking, selected_line, package)
            if response:
                return response
            response = self._post_line(selected_line)
            if response:
                return response
            return self._response_for_select_move(picking)
        message = self.msg_store.create_new_pack_ask_confirmation(barcode)
        return self._response_for_confirm_new_package(
            picking, selected_line, new_package_name=barcode, message=message
        )


class ShopfloorReceptionValidator(Component):
    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.reception.validator"
    _usage = "reception.validator"

    def start(self):
        return {}

    def scan_document(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_stock_pickings(self):
        return {}

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def manual_select_move(self):
        return {
            "move_id": {"required": True, "type": "integer"},
        }

    def set_lot(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "lot_name": {"type": "string"},
            "expiration_date": {"type": "string"},
        }

    def set_quantity(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "quantity": {"type": "float"},
            "barcode": {"type": "string"},
            "confirmation": {"type": "string", "nullable": True},
        }

    def set_quantity__cancel_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
        }

    def process_with_existing_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "quantity": {"coerce": to_float, "type": "float"},
        }

    def process_with_new_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "quantity": {"coerce": to_float, "type": "float"},
        }

    def process_without_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "quantity": {"coerce": to_float, "type": "float"},
        }

    def set_destination(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "location_name": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean"},
        }

    def select_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "barcode": {"type": "string", "required": True},
            "confirmation": {"type": "boolean"},
        }

    def done_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean"},
        }

    def set_lot_confirm_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.reception.validator.response"
    _usage = "reception.validator.response"

    _start_state = "select_document"

    # STATES

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "select_document": self._schema_select_document,
            "manual_selection": self._schema_manual_selection,
            "select_move": self._schema_select_move,
            "confirm_done": self._schema_confirm_done,
            "set_lot": self._schema_set_lot,
            "set_quantity": self._schema_set_quantity,
            "set_destination": self._schema_set_destination,
            "select_dest_package": self._schema_select_dest_package,
            "confirm_new_package": self._schema_confirm_new_package,
        }

    def _start_next_states(self):
        return {"select_document"}

    def _scan_document_next_states(self):
        return {
            "select_document",
            "select_move",
            "set_lot",
            "set_quantity",
            "manual_selection",
        }

    def _list_stock_pickings_next_states(self):
        return {
            "select_document",
            "select_move",
            "set_lot",
            "set_quantity",
            "manual_selection",
        }

    def _scan_line_next_states(self):
        return {"select_move", "set_lot", "set_quantity"}

    def _set_lot_next_states(self):
        return {"select_move", "set_lot", "set_quantity"}

    def _set_quantity_next_states(self):
        return {"set_quantity", "select_move", "set_destination"}

    def _set_quantity__cancel_action_next_states(self):
        return {"set_quantity", "select_move"}

    def _set_destination_next_states(self):
        return {"set_destination", "select_move"}

    def _select_dest_package_next_states(self):
        return {"set_lot", "select_dest_package", "confirm_new_package", "select_move"}

    def _done_next_states(self):
        return {"select_document", "select_move", "confirm_done"}

    def _set_lot_confirm_action_next_states(self):
        return {"set_lot", "set_quantity"}

    def _process_with_existing_pack_next_states(self):
        return {"set_quantity", "select_dest_package"}

    def _process_with_new_pack_next_states(self):
        return {"set_quantity", "set_destination"}

    def _process_without_pack_next_states(self):
        return {"set_quantity", "set_destination"}

    # SCHEMAS

    @property
    def _schema_select_document(self):
        return {
            "pickings": self.schemas._schema_list_of(
                self.schemas.picking(), required=True
            )
        }

    @property
    def _schema_manual_selection(self):
        return {
            "pickings": self.schemas._schema_list_of(
                self.schemas.picking(), required=True
            )
        }

    @property
    def _schema_select_move(self):
        return {
            "picking": self.schemas._schema_dict_of(
                self._schema_stock_picking_with_lines(), required=True
            )
        }

    @property
    def _schema_confirm_done(self):
        return {
            "picking": self.schemas._schema_dict_of(
                self._schema_stock_picking_with_lines(), required=True
            )
        }

    @property
    def _schema_set_lot(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
        }

    @property
    def _schema_set_quantity(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "confirmation_required": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
        }

    @property
    def _schema_set_quantity__cancel_action(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_set_destination(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_select_dest_package(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "packages": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": self.schemas.package(with_packaging=True),
                },
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_confirm_new_package(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": self.schemas._schema_dict_of(
                self._schema_stock_picking_with_lines(), required=True
            ),
            "new_package_name": {"type": "string"},
        }

    def _schema_stock_picking_with_lines(self, lines_with_packaging=False):
        # TODO: ideally, we should use self.schemas_detail.picking_detail
        # instead of this method.
        schema = self.schemas.picking()
        schema.update({"moves": self.schemas._schema_list_of(self.schemas.move())})
        return schema

    # ENDPOINTS

    def start(self):
        return self._response_schema(next_states=self._start_next_states())

    def scan_document(self):
        return self._response_schema(next_states=self._scan_document_next_states())

    def list_stock_pickings(self):
        return self._response_schema(
            next_states=self._list_stock_pickings_next_states()
        )

    def scan_line(self):
        return self._response_schema(next_states=self._scan_line_next_states())

    def manual_select_move(self):
        return self._response_schema(next_states=self._scan_line_next_states())

    def set_lot(self):
        return self._response_schema(next_states=self._set_lot_next_states())

    def set_lot_confirm_action(self):
        return self._response_schema(
            next_states=self._set_lot_confirm_action_next_states()
        )

    def set_quantity(self):
        return self._response_schema(next_states=self._set_quantity_next_states())

    def set_quantity__cancel_action(self):
        return self._response_schema(
            next_states=self._set_quantity__cancel_action_next_states()
        )

    def process_with_existing_pack(self):
        return self._response_schema(
            next_states=self._process_with_existing_pack_next_states()
        )

    def process_with_new_pack(self):
        return self._response_schema(
            next_states=self._process_with_new_pack_next_states()
        )

    def process_without_pack(self):
        return self._response_schema(
            next_states=self._process_without_pack_next_states()
        )

    def set_destination(self):
        return self._response_schema(next_states=self._set_destination_next_states())

    def select_dest_package(self):
        return self._response_schema(
            next_states=self._select_dest_package_next_states()
        )

    def done_action(self):
        return self._response_schema(next_states=self._done_next_states())
