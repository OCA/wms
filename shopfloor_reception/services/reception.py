# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


import pytz

from odoo import fields

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

    def _move_line_by_product(self, product):
        return self.env["stock.move.line"].search(
            self._domain_move_line_by_product(product)
        )

    def _move_line_by_packaging(self, packaging):
        return self.env["stock.move.line"].search(
            self._domain_move_line_by_packaging(packaging)
        )

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
        self._assign_user_to_picking(picking)
        data = {"picking": self._data_for_stock_picking(picking, with_lines=True)}
        return self._response(next_state="select_move", data=data, message=message)

    def _response_for_confirm_done(self, picking, message=None):
        self._assign_user_to_picking(picking)
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

    def _select_document_from_product(self, product):
        """Select the document by product

        next states:
            - set_lot: a single picking has been found for this packaging
            - select_document: A single or no pickings has been found for this packaging
        """
        move_lines = self._move_line_by_product(product).filtered(
            lambda l: l.picking_id.picking_type_id.id in self.picking_types.ids
        )
        pickings = move_lines.mapped("move_id.picking_id")
        if len(pickings) == 1:
            self._assign_user_to_picking(pickings)
            if product.tracking not in ("lot", "serial"):
                return self._response_for_set_quantity(pickings, move_lines)
            return self._response_for_set_lot(pickings, move_lines)
        elif len(pickings) > 1:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        # If no available picking with the right state has been found,
        # return an error
        return self._response_for_select_document(
            message=self.msg_store.product_not_found_in_pickings()
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
        pickings = move_lines.mapped("move_id.picking_id")
        if len(pickings) == 1:
            self._assign_user_to_picking(pickings)
            if packaging.product_id.tracking not in ("lot", "serial"):
                return self._response_for_set_quantity(pickings, move_lines)
            return self._response_for_set_lot(pickings, move_lines)
        elif len(pickings) > 1:
            return self._response_for_select_document(
                pickings=pickings,
                message=self.msg_store.multiple_picks_found_select_manually(),
            )
        # If no available picking with the right state has been found,
        # return a barcode not found error message
        return self._response_for_select_document(
            message=self.msg_store.no_transfer_for_packaging(),
        )

    def _select_line_from_product(self, picking, move, product):
        line = fields.first(
            picking.move_line_ids.filtered(
                lambda l: l.product_id == product
                and not l.result_package_id
                and l.shopfloor_user_id.id in [False, self.env.uid]
            )
        )
        if line:
            # The line quantity to do needs to correspond to
            # the remaining quantity to do of its move.
            line.product_uom_qty = move.product_uom_qty - move.quantity_done
        else:
            qty_todo_remaining = move.product_uom_qty - move.quantity_done
            values = move._prepare_move_line_vals(quantity=qty_todo_remaining)
            line = self.env["stock.move.line"].create(values)
        self._assign_user_to_picking(picking)
        self._assign_user_to_line(line)
        line.qty_done += 1
        if product.tracking not in ("lot", "serial"):
            return self._response_for_set_quantity(picking, line)
        return self._response_for_set_lot(picking, line)

    def _select_line_from_packaging(self, picking, move, packaging):
        line = fields.first(
            picking.move_line_ids.filtered(
                lambda l: l.package_id.product_packaging_id == packaging
                and not l.result_package_id
                and l.shopfloor_user_id.id in [False, self.env.uid]
            )
        )
        if line:
            # The line quantity to do needs to correspond to
            # the remaining quantity to do of its move.
            line.product_uom_qty = move.product_uom_qty - move.quantity_done
        else:
            qty_to_do = move.product_uom_qty - move.quantity_done
            values = move._prepare_move_line_vals(quantity=qty_to_do)
            line = self.env["stock.move.line"].create(values)
        self._assign_user_to_picking(picking)
        self._assign_user_to_line(line)
        line.qty_done += packaging.qty
        if packaging.product_id.tracking not in ("lot", "serial"):
            return self._response_for_set_quantity(picking, line)
        return self._response_for_set_lot(picking, line)

    def _order_stock_picking(self):
        # We sort by scheduled date first. However, there might be a case
        # where two pickings have the exact same scheduled date.
        # In that case, we sort by id.
        return "scheduled_date ASC, id ASC"

    def _scan_document__by_picking(self, barcode):
        search = self._actions_for("search")
        picking_filter_result = search.picking_from_scan(barcode, use_origin=True)
        reception_pickings = picking_filter_result.filtered(
            lambda p: p.picking_type_id.id in self.picking_types.ids
        )
        if picking_filter_result and not reception_pickings:
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

    def _scan_document__by_product(self, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
        if product:
            return self._select_document_from_product(product)

    def _scan_document__by_packaging(self, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            return self._select_document_from_packaging(packaging)

    def _scan_line__by_product(self, picking, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
        if product:
            move = picking.move_lines.filtered(lambda m: m.product_id == product)
            message = self._check_move_available(move, "product")
            if message:
                return self._response_for_select_move(
                    picking,
                    message=message,
                )
            return self._select_line_from_product(picking, move, product)

    def _scan_line__by_packaging(self, picking, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            move = picking.move_lines.filtered(
                lambda m: packaging in m.product_id.packaging_ids
            )
            message = self._check_move_available(move, "packaging")
            if message:
                return self._response_for_select_move(
                    picking,
                    message=message,
                )
            return self._select_line_from_packaging(picking, move, packaging)

    def _check_move_available(self, move, message_code="product"):
        if not move and message_code == "product":
            return self.msg_store.product_not_found_or_already_in_dest_package()
        if not move and message_code == "packaging":
            return self.msg_store.packaging_not_found_or_already_in_dest_package()
        line_without_package = any(
            not ml.result_package_id for ml in move.move_line_ids
        )
        if move.product_uom_qty - move.quantity_done < 1 and not line_without_package:
            return self.msg_store.move_already_done()

    def _set_quantity__by_product(self, picking, selected_line, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
        if product:
            if product.id != selected_line.product_id.id:
                return self._response_for_set_quantity(
                    picking,
                    selected_line,
                    message=self.msg_store.wrong_record(product),
                )
            selected_line.qty_done += 1
            return self._response_for_set_quantity(picking, selected_line)

    def _set_quantity__by_packaging(self, picking, selected_line, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            if packaging.product_id.id != selected_line.product_id.id:
                return self._response_for_set_quantity(
                    picking,
                    selected_line,
                    message=self.msg_store.wrong_record(packaging),
                )
            selected_line.qty_done += packaging.qty
            return self._response_for_set_quantity(picking, selected_line)

    def _set_quantity__by_package(self, picking, selected_line, barcode):
        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if package:
            dest_location = selected_line.location_dest_id
            child_locations = self.env["stock.location"].search(
                [("id", "child_of", dest_location.id)]
            )
            pack_location = package.location_id
            if pack_location:
                if pack_location not in child_locations:
                    # If the scanned package has a location that isn't a child
                    # of the move dest, return an error
                    message = self.msg_store.dest_location_not_allowed()
                    return self._response_for_set_quantity(
                        picking, selected_line, message=message
                    )
                else:
                    # If the scanned package has a valid destination,
                    # set both package and destination on the package,
                    # and go back to the selection line screen
                    selected_line.result_package_id = package
                    selected_line.location_dest_id = pack_location
                    return self._response_for_select_move(picking)
            # Scanned package has no location, move to the location selection
            # screen
            selected_line.result_package_id = package
            return self._response_for_set_destination(picking, selected_line)

    def _set_quantity__by_location(self, picking, selected_line, barcode):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if location:
            dest_location = selected_line.location_dest_id
            child_locations = self.env["stock.location"].search(
                [("id", "child_of", dest_location.id)]
            )
            if location not in child_locations:
                # Scanned location isn't a child of the move's dest location
                message = self.msg_store.dest_location_not_allowed()
                return self._response_for_set_quantity(
                    picking, selected_line, message=message
                )
            # process without pack, set destination location, and go back to
            # `select_move`
            selected_line.location_dest_id = location
            return self._response_for_select_move(picking)

    def _use_handlers(self, handlers, *args, **kwargs):
        for handler in handlers:
            response = handler(*args, **kwargs)
            if response:
                return response

    def _assign_user_to_picking(self, picking):
        picking.user_id = self.env.user

    def _assign_user_to_line(self, line):
        line.shopfloor_user_id = self.env.user

    # DATA METHODS

    def _data_for_stock_picking(self, picking, with_lines=False):
        data = self.data.picking(picking, with_progress=True)
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

    def _response_for_set_quantity(self, picking, line, message=None):
        return self._response(
            next_state="set_quantity",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

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

    def scan_document(self, barcode):
        """Scan a picking, a product or a packaging.

        Input:
            barcode: the barcode of a product, a packaging or a picking name

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
        handlers = (
            self._scan_document__by_picking,
            self._scan_document__by_product,
            self._scan_document__by_packaging,
        )
        response = self._use_handlers(handlers, barcode)
        if response:
            return response
        # If nothing has been found, return a barcode not found error message
        return self._response_for_select_document(
            message=self.msg_store.barcode_not_found()
        )

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
            barcode: The barcode of a product or a packaging

        transitions:
          - select_move: Error: barcode not found
          - set_lot: Packaging / Product has been scanned. Tracked product
          - set_quantity: Packaging / Product has been scanned. Not tracked product
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_move(picking, message=message)
        handlers = (
            self._scan_line__by_product,
            self._scan_line__by_packaging,
        )
        response = self._use_handlers(handlers, picking, barcode)
        if response:
            return response
        # Nothing has been found, return an error
        return self._response_for_select_move(
            picking, message=self.msg_store.barcode_not_found()
        )

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
        if not confirmation:
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
        self._handle_backorder(picking)
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(picking)
        )

    def _handle_backorder(self, picking):
        """This method handles backorders that could be created at picking confirm."""
        backorders_before = picking.backorder_ids
        picking._action_done()
        backorders_after = picking.backorder_ids - backorders_before
        # Remove user_id on the backorder, if any
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
        return self._response_for_set_quantity(picking, selected_line)

    def _check_expiry_date(self, line):
        use_expiration_date = (
            line.product_id.use_expiration_date or line.lot_id.use_expiration_date
        )
        if use_expiration_date and not line.expiration_date:
            return self.msg_store.expiration_date_missing()

    def set_quantity(
        self,
        picking_id,
        selected_line_id,
        quantity=None,
        barcode=None,
        confirmation=False,
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
        if quantity:
            # We set qty_done to be equal to the qty of the picker
            # at the moment of the scan.
            selected_line.qty_done = quantity
        if barcode:
            # Then, we add the qty of whatever was scanned
            # on top of the qty of the picker.
            handlers = (
                self._set_quantity__by_product,
                self._set_quantity__by_packaging,
                self._set_quantity__by_package,
                self._set_quantity__by_location,
            )
            response = self._use_handlers(handlers, picking, selected_line, barcode)
            if response:
                return response
            # Nothing found, ask user if we should create a new pack for the scanned
            # barcode
            if not confirmation:
                return self._response_for_set_quantity(
                    picking,
                    selected_line,
                    message=self.msg_store.create_new_pack_ask_confirmation(barcode),
                )
            package = self.env["stock.quant.package"].create({"name": barcode})
            selected_line.result_package_id = package
            return self._response_for_set_destination(picking, selected_line)
        return self._response_for_set_quantity(
            picking, selected_line, message=self.msg_store.barcode_not_found()
        )

    def process_with_existing_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        new_line, qty_check = selected_line._split_qty_to_be_done(
            quantity, lot_id=False, shopfloor_user_id=False, expiration_date=False
        )
        if qty_check == "greater":
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.unable_to_pick_more(
                    selected_line.product_uom_qty
                ),
            )
        selected_line.qty_done = quantity
        return self._response_for_select_dest_package(picking, selected_line)

    def process_with_new_pack(self, picking_id, selected_line_id, quantity):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_line, message=message
            )
        new_line, qty_check = selected_line._split_qty_to_be_done(
            quantity, lot_id=False, shopfloor_user_id=False, expiration_date=False
        )
        if qty_check == "greater":
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.unable_to_pick_more(
                    selected_line.product_uom_qty
                ),
            )
        selected_line.qty_done = quantity
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
        new_line, qty_check = selected_line._split_qty_to_be_done(
            quantity, lot_id=False, shopfloor_user_id=False, expiration_date=False
        )
        if qty_check == "greater":
            return self._response_for_set_quantity(
                picking,
                selected_line,
                message=self.msg_store.unable_to_pick_more(
                    selected_line.product_uom_qty
                ),
            )
        selected_line.qty_done = quantity
        return self._response_for_set_destination(picking, selected_line)

    def _auto_post_line(self, selected_line, picking):
        new_move = selected_line.move_id.split_other_move_lines(
            selected_line, intersection=True
        )
        new_move.extract_and_action_done()
        # TODO: by using split_other_move_lines above in reception,
        # we encounter a strange behaviour where a line is created in the original picking
        # with qty_done=0 and no related move_id.
        # This is probably caused by package_level_id.

        # The workaround is to look for any orphan lines and delete them,
        # but this should be investigated to find a better solution.
        lines = picking.move_line_ids.filtered(
            lambda l: l.product_id == selected_line.product_id
        )
        for line in lines:
            if not line.move_id:
                line.unlink()

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
        move_dest_location = selected_line.location_dest_id
        move_child_locations = self.env["stock.location"].search(
            [("id", "child_of", move_dest_location.id)]
        )
        pick_type_dest_location = picking.picking_type_id.default_location_dest_id
        pick_type_child_locations = self.env["stock.location"].search(
            [("id", "child_of", pick_type_dest_location.id)]
        )
        if location not in move_child_locations | pick_type_child_locations:
            return self._response_for_set_destination(
                picking,
                selected_line,
                message=self.msg_store.dest_location_not_allowed(),
            )
        if location in move_child_locations:
            # If location is a child of move's dest location, assign it without asking
            selected_line.location_dest_id = location
        elif location in pick_type_child_locations:
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
        if self.work.menu.auto_post_line:
            # If option auto_post_line is active in the shopfloor menu,
            # create a split order with this line.
            self._auto_post_line(selected_line, picking)
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
            selected_line.result_package_id = package
            if self.work.menu.auto_post_line:
                # If option auto_post_line is active in the shopfloor menu,
                # create a split order with this line.
                self._auto_post_line(selected_line, picking)
            return self._response_for_select_move(picking)
        message = self.msg_store.create_new_pack_ask_confirmation(barcode)
        self._assign_user_to_picking(picking)
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
            "confirmation": {"type": "boolean"},
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

    def _set_destination_next_states(self):
        return {"set_destination", "select_move"}

    def _select_dest_package_next_states(self):
        return {"set_lot", "select_dest_package", "confirm_new_package", "select_move"}

    def _done_next_states(self):
        return {"select_document", "select_move", "confirm_done"}

    def _set_lot_confirm_action_next_states(self):
        return {"set_lot", "set_quantity"}

    def _process_with_existing_pack_next_states(self):
        return {"select_dest_package"}

    def _process_with_new_pack_next_states(self):
        return {"set_destination"}

    def _process_without_pack_next_states(self):
        return {"set_destination"}

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

    def set_lot(self):
        return self._response_schema(next_states=self._set_lot_next_states())

    def set_lot_confirm_action(self):
        return self._response_schema(
            next_states=self._set_lot_confirm_action_next_states()
        )

    def set_quantity(self):
        return self._response_schema(next_states=self._set_quantity_next_states())

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
