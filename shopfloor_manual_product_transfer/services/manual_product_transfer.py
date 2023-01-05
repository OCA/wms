# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import UserError
from odoo.fields import first
from odoo.tools import float_compare, float_is_zero, float_round

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.shopfloor.utils import to_float


class ManualProductTransfer(Component):
    """
    Methods for the Manual Product Transfer Process

    Move a product or a lot from one location to another location:

    * scan the source location
    * scan a product or a lot from this source location
    * confirm or change the quantity to move
    * scan the destination location

    You will find a sequence diagram describing states and endpoints
    relationships [here](../docs/manual_product_transfer_diag_seq.png).
    Keep [the sequence diagram](../docs/manual_product_transfer_diag_seq.plantuml)
    up-to-date if you change endpoints.

    Expected:

    * Product or lot is moved to the destination location

    A new move is created and posted with the scanned product (or lot) and the
    relevant quantity.
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.manual.product.transfer"
    _usage = "manual_product_transfer"
    _description = __doc__

    def _response_for_start(self, message=None):
        """Transition to the 'start' state."""
        return self._response(next_state="start", message=message)

    def _response_for_scan_product(self, location, message=None):
        """Transition to the 'scan_product' state for the given source location."""
        return self._response(
            next_state="scan_product",
            data={"location": self.data.location(location)},
            message=message,
        )

    def _response_for_confirm_quantity(
        self, location, product, quantity, lot=None, message=None
    ):
        """Transition to the 'confirm_quantity' state for the given move line."""
        warning = None
        if not self.work.menu.allow_unreserve_other_moves:
            # If the option "Allow to process reserved quantities" is not enabled
            # we should at least display a warning to the operator to not move
            # the quantity already reserved.
            qty_assigned = self._get_product_qty_assigned(location, product, lot)
            if qty_assigned:
                warning = self.msg_store.qty_assigned_to_preserve(
                    product, qty_assigned
                )["body"]
        data = {
            "location": self.data.location(location),
            "product": self.data.product(product),
            "quantity": quantity,
            "warning": warning,
        }
        if lot:
            data["lot"] = self.data.lot(lot)
        return self._response(
            next_state="confirm_quantity",
            data=data,
            message=message,
        )

    def _response_for_set_quantity(self, move_lines, quantity, message=None):
        """Transition to the 'set_quantity' state for the given move line."""
        return self._response(
            next_state="set_quantity",
            data={
                "move_lines": self.data.move_lines(move_lines),
                "quantity": quantity,
            },
            message=message,
        )

    def _response_for_scan_destination_location(
        self, picking, move_lines, message=None
    ):
        """Transition to the 'scan_destination_location' state
        for the given move lines.
        """
        return self._response(
            next_state="scan_destination_location",
            data={
                "picking": self.data.picking(picking),
                "move_lines": self.data.move_lines(move_lines),
            },
            message=message,
        )

    def scan_source_location(self, barcode):
        """Scan a source location.

        It is the starting point of this scenario.

        If stock has been found in the scanned location, allows to scan a
        product or a lot.

        Transitions:
        * scan_product: to scan a product or a lot stored in the scanned location
        * start: no stock found or wrong barcode
        """
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if not location:
            return self._response_for_start(message=self.msg_store.no_location_found())
        if not self.is_src_location_valid(location):
            return self._response_for_start(
                message=self.msg_store.location_not_allowed()
            )
        quants = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("quantity", ">", 0)]
        )
        if not quants:
            return self._response_for_start(
                message=self.msg_store.location_empty(location)
            )
        return self._response_for_scan_product(location)

    def _find_user_move_lines_domain(self, location, product, lot=None):
        domain = [
            ("location_id", "=", location.id),
            # ("qty_done", ">", 0),
            ("state", "not in", ("cancel", "done")),
            ("shopfloor_user_id", "=", self.env.user.id),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("product_id", "=", product.id),
        ]
        if lot:
            domain.append(("lot_id", "=", lot.id))
        return domain

    def _find_user_move_lines(self, location, product, lot=None):
        """Find move lines processed by the current user."""
        domain = self._find_user_move_lines_domain(location, product, lot)
        return self.env["stock.move.line"].search(domain)

    def _find_location_move_lines_domain(
        self, location, product, lot=None, with_qty_done=False
    ):
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", product.id),
            ("state", "in", ("assigned", "partially_available")),
            ("shopfloor_user_id", "=", False),
        ]
        if lot:
            domain.append(("lot_id", "=", lot.id))
        if with_qty_done:
            domain.append(("qty_done", ">", 0))
        else:
            domain.append(("qty_done", "=", 0))
        return domain

    def _find_location_move_lines(
        self, location, product, lot=None, with_qty_done=False
    ):
        """Find existing move lines in progress related to the source location
        but not linked to any user.
        """
        return self.env["stock.move.line"].search(
            self._find_location_move_lines_domain(location, product, lot, with_qty_done)
        )

    def _get_product_qty(self, location, product, lot=None, free=False):
        """Returns the available quantity for a given location/product/lot.

        The available quantity returned depends on the
        "Allow to process reserved quantities" option, if this one is enabled
        then the method will return the quantity on hands, not taking into
        account the reserved quantities (to be able to unreserve them if needed).
        Otherwise the method will return the actual free quantity.
        """
        product = product.with_context(
            location=location.id, lot_id=lot.id if lot else None
        )
        if free:
            return product.free_qty
        return product.qty_available

    def _get_product_qty_processed(self, location, product, lot=None):
        """Returns the current quantity processed (qty done) by users for the
        given location/product/lot among reserved quantities (existing move lines).
        """
        move_lines = self._find_location_move_lines(
            location, product, lot, with_qty_done=True
        )
        return sum(
            [
                line.product_id.uom_id._compute_quantity(
                    line.qty_done,
                    line.product_uom_id,
                    rounding_method="HALF-UP",
                )
                for line in move_lines
            ]
        )

    def _get_product_qty_assigned(self, location, product, lot=None):
        """Returns the quantity reserved for the given location/product/lot."""
        move_lines = self._find_location_move_lines(location, product, lot)
        qty_assigned = sum([line.product_uom_qty for line in move_lines])
        qty_assigned = float_round(
            qty_assigned,
            precision_rounding=product.uom_id.rounding,
            rounding_method="HALF-UP",
        )
        return qty_assigned

    def _get_initial_qty(self, location, product, lot=None):
        """Compute the initial quantity for the given location/product/lot."""
        if self.work.menu.allow_unreserve_other_moves:
            # If the "Allow to process reserved quantities" is enabled, the
            # initial qty is the available qty (reservation included) from which
            # we substract the qty currently processed (qty_done on move lines)
            current_qty = self._get_product_qty(location, product, lot, free=False)
            done_qty = self._get_product_qty_processed(location, product, lot)
        else:
            # Otherwise we simply use the free qty (without any reservation)
            # available in the location as the initial qty
            current_qty = self._get_product_qty(location, product, lot, free=True)
            done_qty = 0
        return current_qty - done_qty

    def scan_product(self, location_id, barcode):
        """Scan a product or a lot existing in the source location.

        If there is already some work in progress for the scanned product or lot,
        restore it.

        Transitions:
        * confirm_quantity: product or lot was found in the source location
        * scan_product: scanned product or lot is wrong (error)
        """
        location = self.env["stock.location"].browse(location_id).exists()
        if not location:
            return self._response_for_start(message=self.msg_store.record_not_found())
        search = self._actions_for("search")
        initial_qty = None
        # Search by product first
        product = search.product_from_scan(barcode)
        if not product:
            packaging = search.packaging_from_scan(barcode)
            product = packaging.product_id
        if product:
            if product.tracking != "none":
                return self._response_for_scan_product(
                    location,
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            existing_move_lines = self._find_user_move_lines(location, product)
            picking = first(existing_move_lines.picking_id)
            if existing_move_lines:
                return self._response_for_scan_destination_location(
                    picking,
                    picking.move_line_ids & existing_move_lines,
                    message=self.msg_store.recovered_previous_session(),
                )
        # Search by lot
        lots = search.lot_from_scan(barcode, limit=None)
        lot = None
        for lot in lots:
            product = lot.product_id
            existing_move_lines = self._find_user_move_lines(
                location, lot.product_id, lot=lot
            )
            picking = first(existing_move_lines.picking_id)
            if existing_move_lines:
                return self._response_for_scan_destination_location(
                    picking,
                    picking.move_line_ids & existing_move_lines,
                    message=self.msg_store.recovered_previous_session(),
                )
        # Compute the initial quantity
        initial_qty = self._get_initial_qty(location, product, lot)
        # No product available quantity to move
        if (product or lot) and float_is_zero(
            initial_qty, precision_rounding=product.uom_id.rounding
        ):
            return self._response_for_scan_product(
                location, message=self.msg_store.no_product_in_location(location)
            )
        # Available quantity to move
        if initial_qty:
            return self._response_for_confirm_quantity(
                location, product, initial_qty, lot
            )
        # No product or lot found
        return self._response_for_scan_product(
            location, message=self.msg_store.barcode_not_found()
        )

    def _check_quantity(self, location, product, lot, quantity):
        """Check that the input quantity does not exceeds the initial quantity.

        Returns a response with an error message if applicable.
        """
        initial_qty = self._get_initial_qty(location, product, lot)
        if (
            float_compare(
                quantity, initial_qty, precision_rounding=product.uom_id.rounding
            )
            == 1
        ):
            return self._response_for_confirm_quantity(
                location,
                product,
                initial_qty,
                lot,
                message=self.msg_store.qty_exceeds_initial_qty(),
            )

    def _check_quantity_in_stock(self, location, product, quantity, lot=None):
        """Check if there is enough quantity of a product in the location."""
        current_qty = self._get_product_qty(location, product, lot, free=True)
        initial_qty = self._get_initial_qty(location, product, lot)
        quantity_lt_current_qty = (
            float_compare(
                quantity, current_qty, precision_rounding=product.uom_id.rounding
            )
            == -1
        )
        quantity_gte_initial_qty = (
            float_compare(
                quantity, initial_qty, precision_rounding=product.uom_id.rounding
            )
            >= 0
        )
        return quantity_lt_current_qty and quantity_gte_initial_qty

    def set_quantity(self, location_id, product_id, quantity, lot_id=None):
        """Allows to change the initial quantity to move.

        Transitions:
        * confirm_quantity: the move is updated with the new quantity
        * confirm_quantity + error message: the new quantity exceeds the initial qty
        """
        location = self.env["stock.location"].browse(location_id).exists()
        product = self.env["product.product"].browse(product_id).exists()
        lot = None
        if lot_id:
            lot = self.env["stock.production.lot"].browse(lot_id).exists()
        # Get back on the start screen if record IDs do not exist
        if not location or not product or (not lot if lot_id else False):
            return self._response_for_start(message=self.msg_store.record_not_found())
        response = self._check_quantity(location, product, lot, quantity)
        if response:
            return response
        return self._response_for_confirm_quantity(location, product, quantity, lot)

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
        if lot:
            move_vals["restrict_lot_id"] = lot.id
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm(merge=False)
        move.with_context(
            {"force_reservation": self.work.menu.allow_force_reservation}
        )._action_assign()
        assert move.state == "assigned", "The reservation of quantities has failed"
        move.move_line_ids.shopfloor_user_id = self.env.user
        for line in move.move_line_ids:
            line.qty_done = line.product_uom_qty
        return move

    def confirm_quantity(
        self,
        location_id,
        product_id,
        quantity,
        lot_id=None,
        barcode=None,
        confirm=False,
    ):
        """Confirm the quantity to move.

        Done by scanning the product/lot a second time (`barcode`)
        or by clicking the button (`confirm`).

        Transitions:
        * scan_destination_location: quantity is confirmed for the current product/lot
        * confirm_quantity: scanned product or lot is wrong (error)
        """
        location = self.env["stock.location"].browse(location_id).exists()
        product = self.env["product.product"].browse(product_id).exists()
        lot = None
        if lot_id:
            lot = self.env["stock.production.lot"].browse(lot_id).exists()
        # Get back on the start screen if record IDs do not exist
        if not location or not product or (not lot if lot_id else False):
            return self._response_for_start(message=self.msg_store.record_not_found())
        # Check input barcode
        if barcode:
            response = self._confirm_quantity_check_barcode(
                location, product, quantity, lot, barcode
            )
            if response:
                return response
            confirm = True
        # If not confirmed, get back on the same screen (should not happen, this
        # means no barcode is scanned or no confirm button is clicked)
        if not confirm:
            return self._response_for_confirm_quantity(
                location,
                product,
                quantity,
                lot,
            )
        # Check the input quantity
        response = self._check_quantity(location, product, lot, quantity)
        if response:
            return response
        savepoint = self._actions_for("savepoint").new()
        stock = self._actions_for("stock")
        unreserve = self._actions_for("stock.unreserve")
        # Quantity has been confirmed, try to create the move
        # 1. Check there is enough stock in the location to move, otherwise
        #    unreserve existing moves if applicable
        unreserved_moves = self.env["stock.move"].browse()
        if (
            not self._check_quantity_in_stock(location, product, quantity, lot=lot)
            and self.work.menu.allow_unreserve_other_moves
        ):
            # If available qty (qty non reserved) < quantity set => Unreserve
            # other moves for this product and location
            move_lines_to_unreserve = self._find_location_move_lines(
                location, product, lot
            )
            message = unreserve.check_unreserve(
                location, move_lines_to_unreserve, product
            )
            if message:
                savepoint.rollback()
                return self._response_for_start(message=message)
            __, unreserved_moves = unreserve.unreserve_moves(
                move_lines_to_unreserve, self.picking_types
            )
        # 2. Create the move and assign it
        move = self._create_move_from_location(location, product, quantity, lot)
        # 3. If the "Ignore transfers when no put-away is available" is enabled
        #    and no putaway has been computed, rollback the creation of the move
        if self.work.menu.ignore_no_putaway_available and stock.no_putaway_available(
            self.picking_types, move.move_line_ids
        ):
            savepoint.rollback()
            return self._response_for_confirm_quantity(
                location,
                product,
                quantity,
                lot,
                message=self.msg_store.no_putaway_destination_available(),
            )
        # 4. If moves were unreserved -> Reserve them back again
        unreserved_moves.with_context(
            {"force_reservation": self.work.menu.allow_force_reservation}
        )._action_assign()
        savepoint.release()
        return self._response_for_scan_destination_location(
            move.picking_id, move.move_line_ids
        )

    def _confirm_quantity_check_barcode(
        self, location, product, quantity, lot, barcode
    ):
        search = self._actions_for("search")
        # Check if the lot matches if any
        if lot:
            scanned_lot = search.lot_from_scan(barcode, products=product)
            # Barcode is not a lot
            if not scanned_lot:
                return self._response_for_confirm_quantity(
                    location,
                    product,
                    quantity,
                    lot,
                    message=self.msg_store.no_lot_for_barcode(barcode),
                )
            # Barcode is a lot but doesn't match the processed one
            if lot != scanned_lot:
                return self._response_for_confirm_quantity(
                    location,
                    product,
                    quantity,
                    lot,
                    message=self.msg_store.wrong_record(scanned_lot),
                )
            return
        # Search by product
        scanned_product = search.product_from_scan(barcode)
        if not scanned_product:
            packaging = search.packaging_from_scan(barcode)
            scanned_product = packaging.product_id
        # Barcode is not a product
        if not scanned_product:
            return self._response_for_confirm_quantity(
                location,
                product,
                quantity,
                lot,
                message=self.msg_store.no_product_for_barcode(barcode),
            )
        # Barcode is a product but doesn't match the processed one
        if product != scanned_product:
            return self._response_for_confirm_quantity(
                location,
                product,
                quantity,
                lot,
                message=self.msg_store.wrong_record(scanned_product),
            )

    def scan_destination_location(self, move_line_ids, barcode):
        """Scan the destination location and post the move.

        Transitions:
        * start: move has been posted successfully
        * scan_destination_location: scanned location is wrong (error)
        """
        move_lines = self.env["stock.move.line"].browse(move_line_ids).exists()
        # Get back on the start screen if record IDs do not exist
        if not move_lines or move_lines.ids != move_line_ids:
            return self._response_for_start(message=self.msg_store.record_not_found())
        search = self._actions_for("search")
        # Check the scanned destination
        location = search.location_from_scan(barcode)
        if not location:
            return self._response_for_scan_destination_location(
                move_lines.picking_id,
                move_lines,
                message=self.msg_store.no_location_found(),
            )
        if not self.is_dest_location_valid(move_lines.move_id, location):
            return self._response_for_scan_destination_location(
                move_lines.picking_id,
                move_lines,
                message=self.msg_store.location_not_allowed(),
            )
        # Set the destination on move lines
        move_lines.location_dest_id = location
        # Validate the move and get back to the start
        stock = self._actions_for("stock")
        stock.validate_moves(
            move_lines.move_id.with_context(
                {"force_reservation": self.work.menu.allow_force_reservation}
            )
        )
        return self._response_for_start(
            message=self.msg_store.transfer_done_success(move_lines.picking_id)
        )

    def cancel(self, move_line_ids):
        """Cancel the move we created in 'confirm_quantity' step.

        Transitions:
        * start: move has been canceled successfully
        * scan_destination_location: unable to cancel move (error)
        """
        move_lines = self.env["stock.move.line"].browse(move_line_ids).exists()
        # Get back on the start screen if record IDs do not exist
        if not move_lines or move_lines.ids != move_line_ids:
            return self._response_for_start(message=self.msg_store.record_not_found())
        try:
            move_lines.move_id._action_cancel()
        except UserError:
            return self._response_for_scan_destination_location(
                move_lines.picking_id,
                move_lines,
                message=self.msg_store.transfer_canceled_error(move_lines.picking_id),
            )
        else:
            # We can remove the move and its picking if this one is empty
            return self._response_for_start(
                message=self.msg_store.transfer_canceled_success(move_lines.picking_id)
            )


class ShopfloorManualProductTransferValidator(Component):
    """Validators for the Manual Product Transfer endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.manual_product_transfer.validator"
    _usage = "manual_product_transfer.validator"

    def scan_source_location(self):
        return {
            "barcode": {"required": True, "type": "string"},
        }

    def scan_product(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def confirm_quantity(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "lot_id": {"coerce": to_int, "required": False, "type": "integer"},
            "barcode": {"type": "string", "required": False},
            "confirm": {"type": "boolean", "nullable": True, "required": False},
        }

    def set_quantity(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "product_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "lot_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def scan_destination_location(self):
        return {
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def cancel(self):
        return {
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }


class ShopfloorManualProductTransferValidatorResponse(Component):
    """Validators for the Manual Product Transfer endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.manual_product_transfer.validator.response"
    _usage = "manual_product_transfer.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "scan_product": self._schema_scan_product,
            "confirm_quantity": self._schema_confirm_quantity,
            "scan_destination_location": self._schema_scan_destination_location,
        }

    @property
    def _schema_scan_product(self):
        return {
            "location": self.schemas._schema_dict_of(self.schemas.location()),
        }

    @property
    def _schema_confirm_quantity(self):
        return {
            "location": self.schemas._schema_dict_of(self.schemas.location()),
            "product": self.schemas._schema_dict_of(self.schemas.product()),
            "lot": self.schemas._schema_dict_of(self.schemas.lot(), required=False),
            "quantity": {"type": "float", "nullable": True, "required": True},
            "warning": {"type": "string", "nullable": True, "required": False},
        }

    @property
    def _schema_scan_destination_location(self):
        return {
            "picking": self.schemas._schema_dict_of(self.schemas.picking()),
            "move_lines": self.schemas._schema_list_of(self.schemas.move_line()),
        }

    def scan_source_location(self):
        return self._response_schema(next_states={"start", "scan_product"})

    def scan_product(self):
        return self._response_schema(
            next_states={
                "start",
                "scan_product",
                "confirm_quantity",
                "scan_destination_location",
            }
        )

    def confirm_quantity(self):
        return self._response_schema(
            next_states={"start", "confirm_quantity", "scan_destination_location"}
        )

    def set_quantity(self):
        return self._response_schema(next_states={"start", "confirm_quantity"})

    def scan_destination_location(self):
        return self._response_schema(next_states={"start", "scan_destination_location"})
