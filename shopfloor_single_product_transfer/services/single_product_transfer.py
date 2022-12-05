# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

import logging
from functools import wraps

from odoo.osv.expression import AND
from odoo.tools import float_compare

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.component.exception import NoComponentError

_logger = logging.getLogger("shopfloor.services.single_product_transfer")


def with_savepoint(method):
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        savepoint = self._actions_for("savepoint").new()
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

    # TODO check if we can remove allow_create_moves
    _inherit = "base.shopfloor.process"
    _name = "shopfloor.single.product.transfer"
    _usage = "single_product_transfer"
    _description = __doc__

    # Responses

    def _response_for_select_location(self, message=None):
        return self._response(next_state="select_location", message=message)

    def _response_for_select_product(self, location, message=None):
        data = {"location": self.data.location(location)}
        # import pdb; pdb.set_trace()
        return self._response(next_state="select_product", data=data, message=message)

    def _response_for_set_quantity(
        self, move_line, message=None, asking_confirmation=False
    ):
        data = {
            "move_line": self.data.move_line(move_line),
            "asking_confirmation": asking_confirmation,
        }
        return self._response(next_state="set_quantity", data=data, message=message)

    # Handlers

    def _scan_location__location_found(self, location):
        """Check that the location exists."""
        if not location:
            message = self.msg_store.no_location_found()
            return self._response_for_select_location(message=message)

    def _scan_location__check_location(self, location):
        """Check that `location` belongs to the source location of the operation type."""
        locations = self.picking_types.default_location_src_id
        child_locations = self.env["stock.location"].search(
            [("id", "child_of", locations.ids)]
        )
        if location not in (locations | child_locations):
            message = self.msg_store.location_content_unable_to_transfer(location)
            return self._response_for_select_location(message=message)

    def _scan_location__check_stock(self, location):
        """Check if the location has products to move."""
        quants_in_location = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("quantity", ">", 0)]
        )
        if not quants_in_location:
            message = self.msg_store.location_empty(location)
            return self._response_for_select_location(message=message)

    def _scan_product__scan_product(self, location, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
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
        if product:
            response = self._use_handlers(handlers, product, location)
            if response:
                return response

    def _scan_product__check_tracking(self, product, location, lot=None):
        if product.tracking == "lot":
            message = self.msg_store.scan_lot_on_product_tracked_by_lot()
            return self._response_for_select_product(location, message=message)

    def _scan_product__select_move_line_domain(self, product, location, lot=None):
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("state", "in", ("assigned", "partially_available")),
            ("picking_id.user_id", "in", (False, self.env.uid)),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
        ]
        if lot:
            lot_domain = [("lot_id", "=", lot.id)]
            domain = AND([domain, lot_domain])
        return domain

    def _scan_product__select_move_line(self, product, location, lot=None):
        domain = self._scan_product__select_move_line_domain(product, location, lot=lot)
        move_line = self.env["stock.move.line"].search(domain, limit=1)
        if move_line:
            stock = self._actions_for("stock")
            if self.work.menu.no_prefill_qty:
                # First, mark move line as picked with qty_done = 0,
                # so the move wont be split because 0 < qty_done < product_uom_qty
                stock.mark_move_line_as_picked(move_line, quantity=0)
                # Then, set the no prefill qty on the move line
                if lot:
                    qty_done = 1
                else:
                    qty_done = 1
                move_line.qty_done = qty_done
            else:
                stock.mark_move_line_as_picked(move_line)
            return self._response_for_set_quantity(move_line)

    def _scan_product__check_create_move_line(self, product, location, lot=None):
        # TODO this is making the `allow_move_create` flag mandatory, we do not want that
        if not self.is_allow_move_create():
            message = self.msg_store.no_operation_found()
            return self._response_for_select_product(location, message=message)

    def _scan_product__unreserve_move_line(self, product, location, lot=None):
        unreserve = self._actions_for("stock.unreserve")
        if self.work.menu.allow_unreserve_other_moves:
            move_lines = self._find_location_move_lines(location, product, lot=lot)
            response = unreserve.check_unreserve(location, move_lines, product, lot)
            if response:
                return response
            unreserve.unreserve_moves(move_lines, self.picking_types)

    def _scan_product__create_move_line_domain(self, product, location, lot=None):
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("available_quantity", ">", 0),
            # FIXME: handle the scan of packages later
            # this will also prevent the fetch of quants with lots having
            # a package, to check.
            ("package_id", "=", False),
        ]
        if lot:
            lot_domain = [("lot_id", "=", lot.id)]
            domain = AND([domain, lot_domain])
        return domain

    def _scan_product__create_move_line(self, product, location, lot=None):
        quant_domain = self._scan_product__create_move_line_domain(
            product, location, lot=lot
        )
        quants_in_location = self.env["stock.quant"].search(quant_domain)
        available_quantity = sum(quants_in_location.mapped("available_quantity"))
        if available_quantity:
            # Check if available qty > packaging qty if packaging qty is scanned
            move = self._create_move_from_location(
                location, product, available_quantity, lot=lot
            )
            move_line = move.move_line_ids
            response = self._scan_product__check_putaway(move_line)
            if response:
                return response
            return self._response_for_set_quantity(move_line)

    def _scan_product__no_stock_available(
        self, product, location, lot=None, packaging=None
    ):
        message = self.msg_store.no_operation_found()
        return self._response_for_select_product(location, message=message)

    def _scan_product__check_putaway(self, move_line):
        stock = self._actions_for("stock")
        ignore_no_putaway_available = self.work.menu.ignore_no_putaway_available
        no_putaway_available = stock.no_putaway_available(self.picking_types, move_line)
        if ignore_no_putaway_available and no_putaway_available:
            message = self.msg_store.no_putaway_destination_available()
            return self._response_for_select_product(
                move_line.location_id, message=message
            )

    def _scan_product__scan_lot(self, location, barcode):
        search = self._actions_for("search")
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
        lot = search.lot_from_scan(barcode)
        if lot:
            product = lot.product_id
            product_response = self._use_handlers(handlers, product, location, lot=lot)
            if product_response:
                return product_response

    def _use_handlers(self, handlers, *args, **kwargs):
        # TODO: each handler should raise a Shopfloor dedicated exception
        # with the response data attached
        for handler in handlers:
            response = handler(*args, **kwargs)
            if response:
                return response

    # Copied from manual_product_transfer
    def _find_location_move_lines_domain(self, location, product, lot=None):
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("state", "in", ("assigned", "partially_available")),
            ("picking_id.user_id", "in", (False, self.env.uid)),
        ]
        if lot:
            domain = AND([domain, [("lot_id", "=", lot.id)]])
        return domain

    # Copied from manual_product_transfer
    def _find_location_move_lines(self, location, product, lot=None):
        """Find existing move lines in progress related to the source location
        but not linked to any user.
        """
        domain = self._find_location_move_lines_domain(location, product, lot=lot)
        return self.env["stock.move.line"].search(domain)

    # Copied from manual_product_transfer
    def _create_move_from_location(self, location, product, quantity, lot=None):
        picking_type = self.picking_types
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
        move.with_context(
            {"force_reservation": self.work.menu.allow_force_reservation}
        )._action_assign()
        assert move.state == "assigned", "The reservation of quantities has failed"
        move_line = move.move_line_ids
        stock = self._actions_for("stock")
        if self.work.menu.no_prefill_qty:
            # We ensure the qty_done is 0 here, so we can set it manually after
            # to avoid the split of the move line by 'mark_move_line_as_picked'.
            stock.mark_move_line_as_picked(move_line, quantity=0)
            # Just to be explicit
            # TODO add if packaging
            if lot:
                qty_done = 1
            else:
                qty_done = 1
            move_line.qty_done = qty_done
        else:
            stock.mark_move_line_as_picked(move_line)
        return move

    def _set_quantity__check_product_in_line(self, move_line, product, lot=None):
        message = False
        if lot:
            wrong_lot = move_line.lot_id != lot
            if wrong_lot:
                message = self.msg_store.wrong_record(lot._name)
        if move_line.product_id != product:
            message = self.msg_store.wrong_record(product._name)
        if message:
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__check_quantity_done(self, move_line, product, lot=None):
        rounding = product.uom_id.rounding
        qty_done = move_line.qty_done
        qty_todo = move_line.product_uom_qty
        # If qty done is >= qty todo, then there's nothing more to pick
        if float_compare(qty_done, qty_todo, precision_rounding=rounding) >= 0:
            message = self.msg_store.unable_to_pick_more(qty_todo)
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__check_no_prefill_qty(self, move_line, product, lot=None):
        # TODO this is making the `no_prefill_qty` flag mandatory, we do not want that
        if not self.work.menu.no_prefill_qty:
            # If no_prefill_qty is False, then qty_done should have been prefilled
            # with product_uom_qty in the select_product screen
            message = self.msg_store.unable_to_pick_more(move_line.product_uom_qty)
            return self._response_for_set_quantity(move_line, message=message)

    def _set_quantity__increment_qty_done(self, move_line, product, lot=None):
        """Increment the quantity done depending on the item scanned."""
        # TODO use no_prefill_qty option
        # TODO if packaging
        if lot:
            qty_done = 1
        else:
            qty_done = 1
        move_line.qty_done += qty_done
        return self._response_for_set_quantity(move_line)

    def _set_quantity__scan_product_handlers(self):
        return (
            self._set_quantity__check_product_in_line,
            self._set_quantity__check_quantity_done,
            self._set_quantity__check_no_prefill_qty,
            self._set_quantity__increment_qty_done,
        )

    def _set_quantity__scan_product(self, move_line, barcode, confirmation=False):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
        handlers = self._set_quantity__scan_product_handlers()
        if product:
            response = self._use_handlers(handlers, move_line, product)
            if response:
                return response

    def _set_quantity__scan_lot(self, move_line, barcode, confirmation=False):
        search = self._actions_for("search")
        lot = search.lot_from_scan(barcode)
        handlers = self._set_quantity__scan_product_handlers()
        if lot:
            product = lot.product_id
            response = self._use_handlers(handlers, move_line, product, lot=lot)
            if response:
                return response

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

    def _set_quantity__check_location(self, location, move_line, confirmation=False):
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
            # TODO loose dependency on 'shopfloor_checkout_sync' to avoid having
            # yet another glue module. In the long term we should make
            # 'shopfloor_checkout_sync' use events and trash the overrides made
            # on all scenarios.
            self._actions_for("checkout.sync")._sync_checkout(lines, location)
        except NoComponentError:
            pass
        lines.location_dest_id = location
        lines.package_level_id.location_dest_id = location

    def _set_quantity__post_move(self, location, move_line, confirmation=False):
        # TODO qty_done = 0: transfer_no_qty_done
        # TODO qty done < product_qty: transfer_confirm_done
        self._write_destination_on_lines(move_line, location)
        stock = self._actions_for("stock")
        stock.validate_moves(move_line.move_id)
        message = self.msg_store.transfer_done_success(move_line.picking_id)
        return self._response_for_select_product(move_line.location_id, message=message)

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

    def _set_quantity__by_product(self, move_line, barcode, confirmation=False):
        product_handlers = [
            self._set_quantity__scan_product,
            self._set_quantity__scan_lot,
            # scan packaging
        ]
        product_response = self._use_handlers(product_handlers, move_line, barcode)
        if product_response:
            return product_response

    def _set_quantity__by_location(self, move_line, barcode, confirmation=False):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        handlers = [
            self._set_quantity__check_location,
            self._set_quantity__post_move,
        ]
        if location:
            response = self._use_handlers(
                handlers, location, move_line, confirmation=confirmation
            )
            if response:
                return response

    # Endpoints

    def start(self):
        move_line = self._find_user_move_line()
        if move_line:
            message = self.msg_store.recovered_previous_session()
            return self._response_for_set_quantity(move_line, message=message)
        return self._response_for_select_location()

    def scan_location(self, barcode):
        """Scan a source location.

        It is the starting point of this scenario.

        If stock has been found in the scanned location, allows to scan a
        product or a lot.

        Transitions:
        * select_product: to scan a product or a lot stored in the scanned location
        * start: no stock found or wrong barcode
        """
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        handlers = [
            self._scan_location__location_found,
            self._scan_location__check_location,
            self._scan_location__check_stock,
        ]
        response = self._use_handlers(handlers, location)
        if response:
            return response
        return self._response_for_select_product(location)

    @with_savepoint
    def scan_product(self, location_id, barcode):
        """Looks for a move line in the given location, from a barcode."""
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_select_product(location)
        handlers = [
            self._scan_product__scan_product,
            self._scan_product__scan_lot,
        ]
        response = self._use_handlers(handlers, location, barcode)
        if response:
            return response
        message = self.msg_store.barcode_not_found()
        return self._response_for_select_product(location, message=message)

    def scan_product__action_cancel(self):
        return self._response_for_select_location()

    def set_quantity(self, selected_line_id, barcode, confirmation=False):
        """Sets quantity done if a product is scanned,
        or posts the move if a location is scanned.
        """
        move_line = self.env["stock.move.line"].browse(selected_line_id)
        if not move_line.exists():
            # TODO Should probably return to scan_product or scan_location?
            return self._response_for_set_quantity(move_line)
        handlers = [
            # Increment qty done if a product / lot / packaging is scanned
            self._set_quantity__by_product,
            # Post the move if a location is scanned
            self._set_quantity__by_location,
        ]
        response = self._use_handlers(
            handlers, move_line, barcode, confirmation=confirmation
        )
        if response:
            return response
        message = self.msg_store.barcode_not_found()
        return self._response_for_set_quantity(move_line, message=message)

    def set_quantity__action_cancel(self, selected_line_id):
        stock = self._actions_for("stock")
        move_line = self.env["stock.move.line"].browse(selected_line_id).exists()
        stock.unmark_move_line_as_picked(move_line)
        return self._response_for_select_location()


class ShopfloorSingleProductTransferValidator(Component):
    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.single.product.transfer.validator"
    _usage = "single_product_transfer.validator"

    def start(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def scan_product(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_product__action_cancel(self):
        return {}

    def set_quantity(self):
        return {
            "selected_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def set_quantity__action_cancel(self):
        return {
            "selected_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorSingleProductTransferValidatorResponse(Component):
    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.single.product.transfer.validator.response"
    _usage = "single_product_transfer.validator.response"

    _start_state = "select_location"

    def _states(self):
        return {
            "select_location": self._schema_select_location,
            "select_product": self._schema_select_product,
            "set_quantity": self._schema_set_quantity,
        }

    def start(self):
        return self._response_schema(next_states=self._start_next_states())

    def scan_location(self):
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

    def _start_next_states(self):
        return {"select_location", "set_quantity"}

    def _scan_location_next_states(self):
        return {"select_location", "select_product"}

    def _scan_product_next_states(self):
        return {"select_product", "set_quantity"}

    def _scan_product__action_cancel_next_states(self):
        return {"select_location"}

    def _set_quantity_next_states(self):
        return {"set_quantity", "select_product"}

    def _set_quantity__action_cancel_next_states(self):
        return {"select_location"}

    @property
    def _schema_select_location(self):
        return {}

    @property
    def _schema_select_product(self):
        return {"location": {"type": "dict", "schema": self.schemas.location()}}

    @property
    def _schema_set_quantity(self):
        return {
            "move_line": {"type": "dict", "schema": self.schemas.move_line()},
            "asking_confirmation": {"type": "boolean", "nullable": True},
        }
