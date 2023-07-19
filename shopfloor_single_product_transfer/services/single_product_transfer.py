# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
from functools import wraps

from odoo.osv.expression import AND
from odoo.tools import float_compare

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.component.exception import NoComponentError
from odoo.addons.shopfloor.utils import to_float

_logger = logging.getLogger("shopfloor.services.single_product_transfer")


def with_savepoint(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        savepoint = self._actions_for("savepoint").new()
        # TODO: This wrapper depends on the result of the response
        # in order to determine whether it should rollback the changes or not.
        # As the content of the response is generated before rolling back,
        # there will be cases where the response returned to the frontend
        # is not in line with the backend.
        # For now, we are manually modifying the response object before returning
        # errors that will roll back the transaction
        # (see "progress_lines_blacklist" mechanism).
        # However, we should find a better solution for this issue to
        # make sure the information returned to the frontend is always true.
        response = method(self, *args, **kwargs)
        message_type = response.get("message", {}).get("message_type")
        if message_type in ("error", "warning"):
            _logger.info(
                "%(method_name)s returned an error/warning. Transaction rollbacked.",
                {"method_name": method.__name__},
            )
            savepoint.rollback()
        savepoint.release()
        return response

    return wrapper


class ShopfloorSingleProductTransfer(Component):
    """
    Methods for the Single Product Transfer Process

    Move a product or lot from one location to another.

    * scan the source location
    * scan a product/lot/packaging from this source location
    * confirm or change the quantity to move
    * scan the destination location

    You will find a sequence diagram describing states and endpoints
    relationships [here](../docs/diagram.png).
    Keep [the sequence diagram](../docs/diagram.plantuml) up-to-date
    if you change endpoints.

    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.single.product.transfer"
    _usage = "single_product_transfer"
    _description = __doc__

    # Responses

    def _response_for_select_location_or_package(self, message=None):
        return self._response(next_state="select_location_or_package", message=message)

    def _response_for_select_product(
        self,
        location=None,
        package=None,
        message=None,
        popup=None,
        progress_lines_blacklist=None,
    ):
        data = {}
        if location:
            data["location"] = self.data.location(
                location,
                with_operation_progress=True,
                progress_lines_blacklist=progress_lines_blacklist,
            )
        if package:
            data["package"] = self.data.package(
                package,
                with_operation_progress_src=True,
                progress_lines_blacklist=progress_lines_blacklist,
            )
        return self._response(
            next_state="select_product", data=data, message=message, popup=popup
        )

    def _response_for_set_quantity(
        self, move_line, message=None, asking_confirmation=False
    ):
        data = {
            "move_line": self.data.move_line(move_line),
            "asking_confirmation": asking_confirmation,
        }
        return self._response(next_state="set_quantity", data=data, message=message)

    def _response_for_set_location(self, move_line, package, message=None):
        data = {
            "move_line": self.data.move_line(move_line),
            "package": self.data.package(package),
        }
        return self._response(next_state="set_location", data=data, message=message)

    # Handlers

    def _scan_location__location_found(self, location, quants):
        """Check that the location exists."""
        if not location:
            message = self.msg_store.no_location_found()
            return self._response_for_select_location_or_package(message=message)

    def _scan_location__check_location(self, location, quants):
        """Check that `location` belongs to the source location of the operation type."""
        if not self.is_src_location_valid(location):
            message = self.msg_store.location_content_unable_to_transfer(location)
            return self._response_for_select_location_or_package(message=message)

    def _scan_location__check_stock(self, location, quants):
        """Check that the location has products to move."""
        if not quants:
            message = self.msg_store.location_empty(location)
            return self._response_for_select_location_or_package(message=message)

    def _scan_location__check_stock_packages(self, location, quants):
        """Check that there are quants without an assigned package."""
        quant_packages = [quant.package_id for quant in quants]
        if all(quant_packages):
            message = self.msg_store.location_contains_only_packages_scan_one()
            return self._response_for_select_location_or_package(message=message)

    def _scan_location__check_line_packages(self, location, quants):
        """Check that the location has lines without an assigned package."""
        if not self.is_allow_move_create():
            lines_without_package = self.env["stock.move.line"].search(
                [
                    ("location_id", "=", location.id),
                    ("package_id", "=", False),
                    ("state", "in", ["assigned", "partially_available"]),
                    ("picking_id.picking_type_id", "in", self.picking_types.ids),
                ]
            )
            if not lines_without_package:
                message = self.msg_store.location_contains_only_packages_scan_one()
                return self._response_for_select_location_or_package(message=message)

    def _scan_package__check_location(self, package):
        """Check if this package corresponds to any of the allowed locations."""
        if package.location_id and not self.is_src_location_valid(package.location_id):
            message = self.msg_store.package_not_allowed_in_src_location(
                package.name, self.picking_types
            )
            return self._response_for_select_location_or_package(message=message)

    def _scan_package__check_stock(self, package):
        """Check if this package corresponds to any of the allowed locations."""
        if not package.quant_ids:
            message = self.msg_store.package_not_allowed_in_src_location(
                package.name, self.picking_types
            )
            return self._response_for_select_location_or_package(message=message)

    def _scan_product__scan_packaging(self, packaging, location=None, package=None):
        handlers = [
            self._scan_product__check_tracking,
            self._scan_product__select_move_line,
            # If no line is found, we might try to create one,
            # if allow_move_create is True
            self._scan_product__check_create_move_line,
            # First, try to create a move line with the available quantity
            self._scan_product__create_move_line,
            # If no stock is available at first, try to unreserve moves if option
            # allow_unreserve_other_moves is enabled
            self._scan_product__unreserve_move_line,
            # Check again if there's some unreserved qty
            self._scan_product__create_move_line,
            # Then return a `no product available` error
            self._scan_product__no_stock_available,
        ]
        product = packaging.product_id
        return self._use_handlers(
            handlers,
            product,
            location=location,
            package=package,
            packaging=packaging,
        )

    def _scan_product__scan_product(self, product, location=None, package=None):
        handlers = [
            self._scan_product__check_tracking,
            self._scan_product__select_move_line,
            # If no line is found, we might try to create one,
            # if allow_move_create is True
            self._scan_product__check_create_move_line,
            # First, try to create a move line with the available quantity
            self._scan_product__create_move_line,
            # If no stock is available at first, try to unreserve moves if option
            # allow_unreserve_other_moves is enabled
            self._scan_product__unreserve_move_line,
            # Check again if there's some unreserved qty
            self._scan_product__create_move_line,
            # Then return a `no product available` error
            self._scan_product__no_stock_available,
        ]
        return self._use_handlers(handlers, product, location=location, package=package)

    def _scan_product__check_tracking(
        self, product, location=None, package=None, lot=None, packaging=None
    ):
        if product.tracking == "lot":
            message = self.msg_store.scan_lot_on_product_tracked_by_lot()
            return self._response_for_select_product(
                location=location, package=package, message=message
            )

    def _scan_product__select_move_line_domain(
        self, product, location=None, package=None, lot=None
    ):
        domain = [
            ("product_id", "=", product.id),
            ("state", "in", ("assigned", "partially_available")),
            ("picking_id.user_id", "in", (False, self.env.uid)),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
        ]
        return self._add_location_package_lot_domain(
            domain, location=location, package=package, lot=lot
        )

    def _scan_product__select_move_line(
        self, product, location=None, package=None, lot=None, packaging=None
    ):
        move_line = self._select_move_line_from_product(product, location, package, lot)
        if move_line:
            stock = self._actions_for("stock")
            if self.work.menu.no_prefill_qty:
                # First, mark move line as picked with qty_done = 0,
                # so the move wont be split because 0 < qty_done < product_uom_qty
                stock.mark_move_line_as_picked(move_line, quantity=0)
                # Then, set the no prefill qty on the move line
                qty_done = 1
                if packaging:
                    qty_done = packaging.qty
                move_line.qty_done = qty_done
            else:
                stock.mark_move_line_as_picked(move_line)
            return self._response_for_set_quantity(move_line)

    def _select_move_line_from_product(self, product, location, package, lot):
        domain = self._scan_product__select_move_line_domain(
            product, location=location, package=package, lot=lot
        )
        # We add a default order by "id" to avoid the _search method
        # setting up its own order, which will result in an error.
        query = self.env["stock.move.line"]._search(domain, order="id", limit=1)
        # After we retrieve the query, we update the order ourselves.
        order_elems = [
            "stock_move_line__picking_id.user_id",
            "stock_move_line__picking_id.priority DESC",
            "stock_move_line__picking_id.scheduled_date ASC",
            "id DESC",
        ]
        query.order = ",".join(order_elems)
        query_str, query_params = query.select()
        query_str += " FOR UPDATE"
        self.env.cr.execute(query_str, query_params)
        ml_ids = [row[0] for row in self.env.cr.fetchall()]
        move_line = self.env["stock.move.line"].browse(ml_ids)
        return move_line

    def _scan_product__check_create_move_line(
        self, product, location=None, package=None, lot=None, packaging=None
    ):
        if not self.is_allow_move_create():
            message = self.msg_store.no_operation_found()
            return self._response_for_select_product(
                location=location, package=package, message=message
            )

    def _scan_product__unreserve_move_line(
        self, product, location=None, package=None, lot=None, packaging=None
    ):
        unreserve = self._actions_for("stock.unreserve")
        if self.work.menu.allow_unreserve_other_moves:
            move_lines = self._find_location_or_package_move_lines(
                product, location=location, package=package, lot=lot
            )
            response = unreserve.check_unreserve(location, move_lines, product, lot)
            if response:
                return response
            unreserve.unreserve_moves(move_lines, self.picking_types)
        else:
            # If we get there then no qty is available, and we are not allowed to unreserve
            # other moves. No stock available for product.
            return self._scan_product__no_stock_available(
                product,
                location=location,
                package=package,
                lot=lot,
                packaging=packaging,
            )

    def _scan_product__create_move_line(
        self, product, location=None, package=None, lot=None, packaging=None
    ):

        available_quantity = product.with_context(
            location=location.id if location else None,
            package_id=package.id if package else None,
            lot_id=lot.id if lot else None,
        ).free_qty
        is_product_available = (
            float_compare(
                available_quantity,
                packaging.qty if packaging else 1.0,
                precision_rounding=product.uom_id.rounding,
            )
            >= 0
        )
        if is_product_available:
            move = self._create_move_from_location(
                product,
                available_quantity,
                location=location,
                package=package,
                lot=lot,
                packaging=packaging,
            )
            move_line = move.move_line_ids
            response = self._scan_product__check_putaway(move_line)
            if response:
                return response
            return self._response_for_set_quantity(move_line)

    def _scan_product__no_stock_available(
        self, product, location=None, package=None, lot=None, packaging=None
    ):
        message = self.msg_store.no_operation_found()
        return self._response_for_select_product(
            location=location, package=package, message=message
        )

    def _scan_product__check_putaway(self, move_line):
        stock = self._actions_for("stock")
        ignore_no_putaway_available = self.work.menu.ignore_no_putaway_available
        no_putaway_available = stock.no_putaway_available(self.picking_types, move_line)
        if ignore_no_putaway_available and no_putaway_available:
            message = self.msg_store.no_putaway_destination_available()
            return self._response_for_select_product(
                location=move_line.location_id,
                package=move_line.package_id,
                message=message,
                # We blacklist the line that has been created
                # because the transaction will only be rolled back
                # after the response is generated,
                # and we do not want this line in the response.
                progress_lines_blacklist=move_line,
            )

    def _scan_product__scan_lot(self, lot, location=None, package=None):
        handlers = [
            self._scan_product__select_move_line,
            # If no line is found, we might try to create one,
            # only if allow_move_create option is True
            self._scan_product__check_create_move_line,
            # First, try to create a move line with the available quantity
            self._scan_product__create_move_line,
            # If no stock is available at first, try to unreserve moves if option
            # allow_unreserve_other_moves is enabled
            self._scan_product__unreserve_move_line,
            # Check again if there's some unreserved qty
            self._scan_product__create_move_line,
            # Then return a `no product available` error
            self._scan_product__no_stock_available,
        ]
        product = lot.product_id
        product_response = self._use_handlers(
            handlers, product, location=location, package=package, lot=lot
        )
        if product_response:
            return product_response

    def _use_handlers(self, handlers, *args, **kwargs):
        # TODO: each handler should raise a Shopfloor dedicated exception
        # with the response data attached
        for handler in handlers:
            response = handler(*args, **kwargs)
            if response:
                return response

    def _add_location_package_lot_domain(
        self, domain, location=None, package=None, lot=None
    ):
        if location:
            domain = AND([domain, [("location_id", "=", location.id)]])
        if lot:
            domain = AND([domain, [("lot_id", "=", lot.id)]])
        domain = AND([domain, [("package_id", "=", package.id if package else False)]])
        return domain

    # Copied from manual_product_transfer
    def _find_location_or_package_move_lines_domain(
        self, product, location=None, package=None, lot=None
    ):
        domain = [
            ("product_id", "=", product.id),
            ("state", "in", ("assigned", "partially_available")),
            ("picking_id.user_id", "in", (False, self.env.uid)),
        ]
        return self._add_location_package_lot_domain(
            domain, location=location, package=package, lot=lot
        )

    # Copied from manual_product_transfer
    def _find_location_or_package_move_lines(
        self, product, location=None, package=None, lot=None
    ):
        """Find existing move lines in progress related to the source location
        but not linked to any user.
        """
        domain = self._find_location_or_package_move_lines_domain(
            product, location=location, package=package, lot=lot
        )
        return self.env["stock.move.line"].search(domain)

    # Copied from manual_product_transfer
    def _create_move_from_location(
        self, product, quantity, location=None, package=None, lot=None, packaging=None
    ):
        picking_type = self.picking_types
        location = location or package.location_id
        move_vals = {
            "name": product.name,
            "company_id": picking_type.company_id.id,
            "product_id": product.id,
            "product_uom": product.uom_id.id,
            "product_uom_qty": quantity,
            "location_id": location.id,
            "location_dest_id": picking_type.default_location_dest_id.id,
            "origin": self.work.menu.name,
            "picking_type_id": picking_type.id,
        }
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm(merge=False)
        picking = move.picking_id
        if package:
            # When we create a package_level, we force the reservation of the scanned package.
            package_level = self.env["stock.package_level"].create(
                {
                    "picking_id": picking.id,
                    "package_id": package.id,
                    "location_id": package.location_id.id,
                    "location_dest_id": picking.location_dest_id.id,
                    "company_id": picking.company_id.id,
                }
            )
            move.package_level_id = package_level
        move.with_context(
            {"force_reservation": self.work.menu.allow_force_reservation}
        )._action_assign()
        assert move.state == "assigned", "The reservation of quantities has failed"
        # we expect to get only one move line as we are
        # moving only bulk products w/o lot or package.
        move_line = move.move_line_ids[0]
        stock = self._actions_for("stock")
        if self.work.menu.no_prefill_qty:
            # We ensure the qty_done is 0 here, so we can set it manually after
            # to avoid the split of the move line by 'mark_move_line_as_picked'.
            stock.mark_move_line_as_picked(move_line, quantity=0)
            # Set the initial qty_done to 1 for product and lot
            qty_done = 1
            if packaging:
                qty_done = packaging.qty
            move_line.qty_done = qty_done
        else:
            stock.mark_move_line_as_picked(move_line)
        return move

    def _set_quantity__check_product_in_line(
        self, move_line, product, lot=None, packaging=None
    ):
        message = False
        if lot:
            wrong_lot = move_line.lot_id != lot
            if wrong_lot:
                message = self.msg_store.wrong_record(lot)
        if move_line.product_id != product:
            message = self.msg_store.wrong_record(product)
        if message:
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__check_quantity_done(
        self, move_line, location=None, package=None, confirmation=False
    ):
        rounding = move_line.product_id.uom_id.rounding
        qty_done = move_line.qty_done
        qty_todo = move_line.product_uom_qty
        # If qty done is >= qty todo, then there's nothing more to pick
        if float_compare(qty_done, qty_todo, precision_rounding=rounding) > 0:
            message = self.msg_store.unable_to_pick_more(qty_todo)
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__check_no_prefill_qty(
        self, move_line, product, lot=None, packaging=None
    ):
        if not self.work.menu.no_prefill_qty:
            # If no_prefill_qty is False, then qty_done should have been prefilled
            # with product_uom_qty in the select_product screen
            message = self.msg_store.unable_to_pick_more(move_line.product_uom_qty)
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__increment_qty_done(
        self, move_line, product, lot=None, packaging=None
    ):
        """Increment the quantity done depending on the item scanned."""
        # When we reach this handler, the 'no_prefill_qty' is enabled
        # For product or lot, we increment by 1 by default
        qty_done = 1
        if packaging:
            qty_done = packaging.qty
        move_line.qty_done += qty_done
        return self._response_for_set_quantity(move_line)

    def _set_quantity__set_picker_qty(self, move_line, quantity):
        """Sets move_line qty_done according to picker quantity."""
        move_line.qty_done = quantity

    def _set_quantity__scan_product_handlers(self):
        return (
            self._set_quantity__check_product_in_line,
            self._set_quantity__increment_qty_done,
        )

    def _set_quantity__by_product(self, move_line, product, confirmation=False):
        handlers = self._set_quantity__scan_product_handlers()
        return self._use_handlers(handlers, move_line, product)

    def _set_quantity__by_lot(self, move_line, lot, confirmation=False):
        handlers = self._set_quantity__scan_product_handlers()
        product = lot.product_id
        return self._use_handlers(handlers, move_line, product, lot=lot)

    def _set_quantity__by_packaging(self, move_line, packaging, confirmation=False):
        handlers = self._set_quantity__scan_product_handlers()
        product = packaging.product_id
        return self._use_handlers(handlers, move_line, product, packaging=packaging)

    def _set_quantity__valid_dest_location_for_move_line_domain(self, move_line):
        move_line_dest_location = move_line.location_dest_id
        return [
            "|",
            ("id", "in", move_line_dest_location.ids),
            ("id", "child_of", move_line_dest_location.ids),
        ]

    def _set_quantity__valid_dest_location_for_move_line(self, move_line):
        domain = self._set_quantity__valid_dest_location_for_move_line_domain(move_line)
        return self.env["stock.location"].search(domain)

    def _valid_dest_location_for_menu_domain(self):
        return [
            "|",
            ("id", "in", self.picking_types.default_location_dest_id.ids),
            ("id", "child_of", self.picking_types.default_location_dest_id.ids),
        ]

    def _valid_dest_location_for_menu(self):
        domain = self._valid_dest_location_for_menu_domain()
        return self.env["stock.location"].search(domain)

    def _set_quantity__check_location(self, move_line, location, confirmation=False):
        valid_locations_for_move_line = (
            self._set_quantity__valid_dest_location_for_move_line(move_line)
        )
        valid_locations_for_menu = self._valid_dest_location_for_menu()
        message = False
        asking_confirmation = False
        if location in valid_locations_for_move_line:
            # scanned location is valid, return no response
            pass
        elif (
            location in valid_locations_for_menu
            and self.work.menu.allow_alternative_destination
        ):
            # Considered valid if scan confirmed
            if not confirmation:
                # Ask for confirmation
                orig_location = move_line.location_dest_id
                message = self.msg_store.confirm_location_changed(
                    orig_location, location
                )
                asking_confirmation = True
        else:
            # Invalid location, return an error
            message = self.msg_store.dest_location_not_allowed()
        if message:
            return self._response_for_set_quantity(
                move_line, message=message, asking_confirmation=asking_confirmation
            )

    def _lock_lines(self, lines):
        self._actions_for("lock").for_update(lines)

    def _write_destination_on_lines(self, lines, location):
        # TODO
        # '_write_destination_on_lines' is implemented in:
        #
        #   - 'location_content_transfer'
        #   - 'zone_picking'
        #   - 'cluster_picking' (but it is called '_unload_write_destination_on_lines')
        #
        # And all of them has a different implementation,
        # To refactor later.
        try:
            # TODO lose dependency on 'shopfloor_checkout_sync' to avoid having
            # yet another glue module. In the long term we should make
            # 'shopfloor_checkout_sync' use events and trash the overrides made
            # on all scenarios.
            checkout_sync = self._actions_for("checkout.sync")
        except NoComponentError:
            self._lock_lines(lines)
        else:
            self._lock_lines(checkout_sync._all_lines_to_lock(lines))
            checkout_sync._sync_checkout(lines, location)
        lines.location_dest_id = location

    def _set_quantity__post_move(self, move_line, location, confirmation=False):
        # TODO qty_done = 0: transfer_no_qty_done
        # TODO qty done < product_qty: transfer_confirm_done
        self._write_destination_on_lines(move_line, location)
        if self.is_allow_move_create():
            self._post_move(move_line)
        else:
            # If allow_move_create is not enabled,
            # we create a backorder.
            self._split_move(move_line)
        message = self.msg_store.transfer_done_success(move_line.picking_id)
        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(move_line)
        return self._response_for_select_product(
            location=move_line.location_id,
            package=move_line.package_id,
            message=message,
            popup=completion_info_popup,
        )

    def _post_move(self, move_line):
        move_line.picking_id.with_context({"cancel_backorder": True})._action_done()

    def _split_move(self, move_line):
        # TODO: when we split the move, we still get a
        # backorder, which should not be the case.
        # See if there's a way to identify the moves
        # generated through this mechanism and avoid creating them.
        move_line._split_partial_quantity()
        new_move = move_line.move_id.split_other_move_lines(
            move_line, intersection=True
        )
        if new_move:
            # A new move is created in case of partial quantity
            new_move.extract_and_action_done()
            return
        # In case of full quantity, post the initial move
        move_line.move_id.extract_and_action_done()

    def _find_user_move_line_domain(self, user):
        return [
            ("picking_id.user_id", "in", (False, self.env.uid)),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("state", "in", ("assigned", "partially_available")),
            ("qty_done", ">", 0),
        ]

    def _find_user_move_line(self):
        """Return the first move line already started (if any)."""
        user = self.env.user
        domain = self._find_user_move_line_domain(user)
        return self.env["stock.move.line"].search(domain, limit=1)

    def _set_quantity__by_location_handlers(self):
        return [
            self._set_quantity__check_location,
            self._set_quantity__post_move,
        ]

    def _set_quantity__by_location(self, move_line, location, confirmation=False):
        # We're about to leave the `set_quantity` screen.
        # First ensure that quantity is valid.
        invalid_qty_response = self._set_quantity__check_quantity_done(move_line)
        if invalid_qty_response:
            return invalid_qty_response
        move_line.result_package_id = False
        handlers = self._set_quantity__by_location_handlers()
        response = self._use_handlers(
            handlers, move_line, location, confirmation=confirmation
        )
        if response:
            return response

    def _set_quantity__by_package(self, move_line, package, confirmation=False):
        # We're about to leave the `set_quantity` screen.
        # First ensure that quantity is valid.
        invalid_qty_response = self._set_quantity__check_quantity_done(move_line)
        if invalid_qty_response:
            return invalid_qty_response
        # If package isn't empty, then check its location then post the move
        if package.quant_ids:
            location = package.location_id
            handlers = self._set_quantity__by_location_handlers()
            response = self._use_handlers(
                handlers, move_line, location, confirmation=confirmation
            )
            move_line.result_package_id = package
            return response
        # Else, go to `set_location` screen
        move_line.result_package_id = package
        return self._response_for_set_location(move_line, package)

    def _scan_location_or_package__by_package(self, package):
        handlers = [
            self._scan_package__check_location,
            self._scan_package__check_stock,
        ]
        response = self._use_handlers(handlers, package)
        if response:
            return response
        return self._response_for_select_product(
            package=package, location=package.location_id
        )

    def _scan_location_or_package__by_location(self, location):
        quants_in_location = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("quantity", ">", 0)]
        )
        handlers = [
            self._scan_location__location_found,
            self._scan_location__check_location,
            self._scan_location__check_stock,
            self._scan_location__check_stock_packages,
            self._scan_location__check_line_packages,
        ]
        response = self._use_handlers(handlers, location, quants_in_location)
        if response:
            return response
        return self._response_for_select_product(location=location)

    # Endpoints

    def start(self):
        move_line = self._find_user_move_line()
        if move_line:
            message = self.msg_store.recovered_previous_session()
            return self._response_for_set_quantity(move_line, message=message)
        return self._response_for_select_location_or_package()

    def scan_location_or_package(self, barcode):
        """Scan a source location or a source package.

        It is the starting point of this scenario.

        If stock has been found in the scanned location, or if a package has been found,
        it allows to scan a product or a lot.

        Transitions:
        * select_product: to scan a product or a lot stored in the scanned location
        * start: no stock found or wrong barcode
        """
        search = self._actions_for("search")
        handlers_by_type = {
            "package": self._scan_location_or_package__by_package,
            "location": self._scan_location_or_package__by_location,
        }
        search_result = search.find(barcode, types=handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(search_result.record)
        message = self.msg_store.barcode_not_found()
        return self._response_for_select_location_or_package(message=message)

    @with_savepoint
    def scan_product(self, barcode, location_id=None, package_id=None):
        """Looks for a move line in the given location or package, from a barcode.

        This endpoint will take either a location_id or a package_id,
        depending on what the user has scanned in the previous screen.
        This will be used as context to handle the scan and apply the necessary checks.

        We will receive either:
            - location_id
            - package_id

        Barcode can be:
            - a product
            - a product packaging
            - a lot
        """
        location = self.env["stock.location"].browse(location_id)
        package = self.env["stock.quant.package"].browse(package_id)
        if not location.exists() and not package.exists():
            return self._response_for_select_location_or_package()
        handlers_by_type = {
            "product": self._scan_product__scan_product,
            "packaging": self._scan_product__scan_packaging,
            "lot": self._scan_product__scan_lot,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, types=handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(search_result.record, location=location, package=package)
        message = self.msg_store.barcode_not_found()
        return self._response_for_select_product(
            location=location, package=package, message=message
        )

    def scan_product__action_cancel(self):
        return self._response_for_select_location_or_package()

    def set_quantity(self, selected_line_id, barcode, quantity, confirmation=False):
        """Sets quantity done if a product is scanned,
        posts the move if a location is scanned
        or moves the products to a package if a package is scanned.
        """
        move_line = self.env["stock.move.line"].browse(selected_line_id)
        if not move_line.exists():
            # TODO Should probably return to scan_product or scan_location?
            return self._response_for_set_quantity(move_line)

        self._lock_lines(move_line)
        if move_line.state == "done":
            message = self.msg_store.move_already_done()
            return self._response_for_set_quantity(move_line, message=message)
        self._set_quantity__set_picker_qty(move_line, quantity)
        handlers_by_type = {
            # Increment qty done if a product / lot / packaging is scanned
            "product": self._set_quantity__by_product,
            "lot": self._set_quantity__by_lot,
            "packaging": self._set_quantity__by_packaging,
            # Post the move if a location is scanned
            "location": self._set_quantity__by_location,
            # Puts the product in a new or an existing pack
            "package": self._set_quantity__by_package,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, types=handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(move_line, search_result.record, confirmation=confirmation)
        message = self.msg_store.barcode_not_found()
        return self._response_for_set_quantity(move_line, message=message)

    def set_quantity__action_cancel(self, selected_line_id):
        move_line = self.env["stock.move.line"].browse(selected_line_id).exists()
        picking = move_line.picking_id
        if self.is_allow_move_create() and self.env.user == picking.create_uid:
            picking.action_cancel()
        else:
            stock = self._actions_for("stock")
            stock.unmark_move_line_as_picked(move_line)
        return self._response_for_select_location_or_package()

    def set_location(self, selected_line_id, package_id, barcode):
        """Sets the destination location
        if a package is scanned using the set_quantity endpoint.
        """
        move_line = self.env["stock.move.line"].browse(selected_line_id)
        handlers_by_type = {
            # Post the move if a location is scanned
            "location": self._set_quantity__by_location,
        }
        search = self._actions_for("search")
        search_result = search.find(barcode, types=handlers_by_type.keys())
        handler = handlers_by_type.get(search_result.type)
        if handler:
            return handler(move_line, search_result.record)
        package = self.env["stock.quant.package"].browse(package_id)
        message = self.msg_store.barcode_not_found()
        return self._response_for_set_location(move_line, package, message=message)


class ShopfloorSingleProductTransferValidator(Component):
    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.single.product.transfer.validator"
    _usage = "single_product_transfer.validator"

    def start(self):
        return {}

    def scan_location_or_package(self):
        return {"barcode": {"required": True, "type": "string"}}

    def scan_product(self):
        return {
            "location_id": {"coerce": to_int, "required": False, "type": "integer"},
            "package_id": {"coerce": to_int, "required": False, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_product__action_cancel(self):
        return {}

    def set_quantity(self):
        return {
            "selected_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def set_quantity__action_cancel(self):
        return {
            "selected_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_location(self):
        return {
            "selected_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }


class ShopfloorSingleProductTransferValidatorResponse(Component):
    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.single.product.transfer.validator.response"
    _usage = "single_product_transfer.validator.response"

    _start_state = "select_location_or_package"

    def _states(self):
        return {
            "select_location_or_package": self._schema_select_location_or_package,
            "select_product": self._schema_select_product,
            "set_quantity": self._schema_set_quantity,
            "set_location": self._schema_set_location,
        }

    def start(self):
        return self._response_schema(next_states=self._start_next_states())

    def scan_location_or_package(self):
        return self._response_schema(next_states=self._scan_location_next_states())

    def scan_product(self):
        return self._response_schema(next_states=self._scan_product_next_states())

    def scan_product__action_cancel(self):
        return self._response_schema(
            next_states=self._scan_product__action_cancel_next_states()
        )

    def set_quantity(self):
        return self._response_schema(next_states=self._set_quantity_next_states())

    def set_quantity__action_cancel(self):
        return self._response_schema(
            next_states=self._set_quantity__action_cancel_next_states()
        )

    def set_location(self):
        return self._response_schema(next_states=self._set_location_next_states())

    def _start_next_states(self):
        return {"select_location_or_package", "set_quantity"}

    def _scan_location_next_states(self):
        return {"select_location_or_package", "select_product"}

    def _scan_product_next_states(self):
        return {"select_product", "set_quantity"}

    def _scan_product__action_cancel_next_states(self):
        return {"select_location_or_package"}

    def _set_quantity_next_states(self):
        return {"set_quantity", "select_product", "set_location"}

    def _set_quantity__action_cancel_next_states(self):
        return {"select_location_or_package"}

    def _set_location_next_states(self):
        return {"set_quantity", "select_product", "set_location"}

    @property
    def _schema_select_location_or_package(self):
        return {}

    @property
    def _schema_select_product(self):
        return {
            "location": {
                "type": "dict",
                "required": False,
                "schema": self.schemas.location(),
            },
            "package": {
                "type": "dict",
                "required": False,
                "schema": self.schemas.package(),
            },
        }

    @property
    def _schema_set_quantity(self):
        return {
            "move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "asking_confirmation": {"type": "boolean", "nullable": True},
        }

    @property
    def _schema_set_location(self):
        return {
            "move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "package": {"type": "dict", "schema": self.schemas.package()},
        }
