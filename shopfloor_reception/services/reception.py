# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Reception(Component):
    """
    Methods for the Reception Process

    You can find a sequence diagram describing states and endpoints relationships
    [here](../docs/reception_sequence_graph.png)
    Keep [the sequence diagram](../docs/reception_sequence_graph.mermaid)
    up-to-date if you change endpoints.
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

    # DOMAIN METHODS

    def _domain_move_line_by_packaging(self, packaging):
        return [
            ("move_id.picking_id.picking_type_id", "in", self.picking_types.ids),
            ("move_id.picking_id.state", "=", "assigned"),
            ("move_id.picking_id.user_id", "=", False),
            ("package_id.product_packaging_id", "=", packaging.id),
        ]

    def _domain_move_line_by_product(self, product):
        return [
            ("move_id.picking_id.picking_type_id", "in", self.picking_types.ids),
            ("move_id.picking_id.state", "=", "assigned"),
            ("move_id.picking_id.user_id", "=", False),
            ("product_id", "=", product.id),
        ]

    def _domain_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
            ("user_id", "=", False),
        ]

    def _select_picking(self, picking):
        if picking.picking_type_id not in self.picking_types:
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if picking.state != "assigned":
            return self._response_for_select_document(
                message=self.msg_store.stock_picking_not_available(picking)
            )
        return self._response_for_select_line(picking)

    def _response_for_select_line(self, picking, message=None):
        picking.user_id = self.env.user
        data = {"picking": self._data_for_stock_picking(picking)}
        return self._response(next_state="select_line", data=data, message=message)

    def _select_document_from_product(self, product):
        """Select the document by product

        next states:
            - set_lot: a single picking has been found for this packaging
            - select_document: A single or no pickings has been found for this packaging
        """
        move_lines = self._move_line_by_product(product)
        pickings = move_lines.mapped("move_id.picking_id")
        if len(pickings) == 1:
            pickings.user_id = self.env.user
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
        move_lines = self._move_line_by_packaging(packaging)
        pickings = move_lines.mapped("move_id.picking_id")
        if len(pickings) == 1:
            pickings.user_id = self.env.user
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

    def _select_line_from_product(self, picking, product):
        lines = picking.move_line_ids.filtered(lambda l: l.product_id == product)
        if not lines:
            return self._response_for_select_line(
                picking,
                message=self.msg_store.product_not_found_in_picking(),
            )
        picking.user_id = self.env.user
        if product.tracking not in ("lot", "serial"):
            return self._response_for_set_quantity(picking, lines)
        return self._response_for_set_lot(picking, lines)

    def _select_line_from_packaging(self, picking, packaging):
        lines = picking.move_line_ids.filtered(
            lambda l: l.package_id.product_packaging_id == packaging
        )
        if not lines:
            return self._response_for_select_line(
                picking,
                message=self.msg_store.packaging_not_found_in_picking(),
            )
        picking.user_id = self.env.user
        if packaging.product_id.tracking not in ("lot", "serial"):
            return self._response_for_set_quantity(picking, lines)
        return self._response_for_set_lot(picking, lines)

    def _order_stock_picking(self):
        return "scheduled_date ASC"

    def _scan_document__scan_picking(self, barcode):
        search = self._actions_for("search")
        picking = search.picking_from_scan(barcode)
        if picking:
            return self._select_picking(picking)

    def _scan_document__scan_product(self, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        if product:
            return self._select_document_from_product(product)

    def _scan_document__scan_packaging(self, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            return self._select_document_from_packaging(packaging)

    def _scan_line__scan_product(self, picking, barcode):
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        if product:
            return self._select_line_from_product(picking, product)

    def _scan_line__scan_packaging(self, picking, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            return self._select_line_from_packaging(picking, packaging)

    def _set_quantity__scan_product(self, picking, selected_lines, barcode):
        # needed values:
        # selected_lines
        # picking
        search = self._actions_for("search")
        product = search.product_from_scan(barcode, use_packaging=False)
        if product:
            selected_lines.qty_done += 1
            return self._response_for_set_quantity(picking, selected_lines)

    def _set_quantity__scan_packaging(self, picking, selected_lines, barcode):
        search = self._actions_for("search")
        packaging = search.packaging_from_scan(barcode)
        if packaging:
            selected_lines.qty_done += packaging.qty
            return self._response_for_set_quantity(picking, selected_lines)

    def _set_quantity__scan_package(self, picking, selected_lines, barcode):
        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if package:
            dest_location = selected_lines.location_dest_id
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
                        picking, selected_lines, message=message
                    )
                else:
                    # If the scanned package has a valid destination,
                    # set both package and destination on the package,
                    # and go back to the selection line screen
                    selected_lines.result_package_id = package
                    selected_lines.location_dest_id = pack_location
                    return self._response_for_select_line(picking)
            # Scanned package has no location, move to the location selection
            # screen
            selected_lines.result_package_id = package
            return self._response_for_set_destination(picking, selected_lines)

    def _set_quantity__scan_location(self, picking, selected_lines, barcode):
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if location:
            dest_location = selected_lines.location_dest_id
            child_locations = self.env["stock.location"].search(
                [("id", "child_of", dest_location.id)]
            )
            if location not in child_locations:
                # Scanned location isn't a child of the move's dest location
                message = self.msg_store.dest_location_not_allowed()
                return self._response_for_set_quantity(
                    picking, selected_lines, message=message
                )
            # process without pack, set destination location, and go back to
            # `select_line`
            selected_lines.location_dest_id = location
            return self._response_for_select_line(picking)

    def _use_handlers(self, handlers, *args, **kwargs):
        for handler in handlers:
            response = handler(*args, **kwargs)
            if response:
                return response

    # DATA METHODS

    def _data_for_stock_picking(self, picking):
        data = self.data.picking(picking)
        data.update({"move_lines": self._data_for_move_lines(picking.move_line_ids)})
        return data

    def _data_for_stock_pickings(self, pickings):
        return [self._data_for_stock_picking(picking) for picking in pickings]

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    # RESPONSES

    def _response_for_select_document(self, pickings=None, message=None):
        if not pickings:
            pickings = self.env["stock.picking"].search(
                self._domain_stock_picking(),
                order=self._order_stock_picking(),
            )
        data = {"pickings": self._data_for_stock_pickings(pickings)}
        return self._response(next_state="select_document", data=data, message=message)

    def _response_for_set_lot(self, picking, lines, message=None):
        # If the product isn't tracked, move to the next screen
        return self._response(
            next_state="set_lot",
            data={
                "selected_move_lines": self._data_for_move_lines(lines),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _response_for_set_quantity(self, picking, lines, message=None):
        return self._response(
            next_state="set_quantity",
            data={
                "selected_move_lines": self._data_for_move_lines(lines),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _response_for_set_destination(self, picking, lines, message=None):
        return self._response(
            next_state="set_destination",
            data={
                "selected_move_lines": self._data_for_move_lines(lines),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _response_for_select_dest_package(self, picking, lines, message=None):
        return self._response(
            next_state="select_dest_package",
            data={
                "selected_move_lines": self._data_for_move_lines(lines),
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
          - select_line: Picking scanned, one has been found
          - set_lot: Packaging / Product has been scanned,
                     single correspondance. Tracked product
          - set_quantity: Packaging / Product has been scanned,
                          single correspondance. Not tracked product
        """
        self._actions_for("search")
        handlers = [
            self._scan_document__scan_picking,
            self._scan_document__scan_product,
            self._scan_document__scan_packaging,
        ]
        response = self._use_handlers(handlers, barcode)
        if response:
            return response
        # If nothing has been found, return a barcode not found error message
        return self._response_for_select_document(
            message=self.msg_store.barcode_not_found()
        )

    def scan_line(self, picking_id, barcode):
        """Scan a product or a packaging

        input:
            barcode: The barcode of a product or a packaging

        transitions:
          - select_line: Error: barcode not found
          - set_lot: Packaging / Product has been scanned. Tracked product
          - set_quantity: Packaging / Product has been scanned. Not tracked product
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_line(picking, message=message)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_line(picking, message=message)
        handlers = [
            self._scan_line__scan_product,
            self._scan_line__scan_packaging,
        ]
        response = self._use_handlers(handlers, picking, barcode)
        if response:
            return response
        # Nothing has been found, return an error
        return self._response_for_select_line(
            picking, message=self.msg_store.barcode_not_found()
        )

    def done_action(self, picking_id, confirmation=False):
        picking = self.env["stock.picking"].browse(picking_id)
        if all(line.qty_done == 0 for line in picking.move_line_ids):
            # If no line has been processed, refuse to set the picking as done
            return self._response_for_select_line(
                picking, message=self.msg_store.transfer_no_qty_done()
            )
        if not confirmation:
            to_backorder = picking._check_backorder()
            if to_backorder:
                # Not all lines are fully done, ask the user to confirm the
                # backorder creation
                return self._response_for_select_line(
                    picking, message=self.msg_store.transfer_confirm_done()
                )
            # all lines are done, ask the user to confirm anyway
            return self._response_for_select_line(
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
        self, picking_id, selected_line_ids, lot_name=None, expiration_date=None
    ):
        """Set lot and its expiration date

        Input:
            barcode: The barcode of a lot
            expiration_date: The expiration_date

        transitions:
          - select_line: User clicked on back
          - set_lot: Barcode not found. Ask user to create one from barcode
          - set_lot: expiration_date has been set on the selected line
          - set_lot: lot_it has been set on the selected line
          - set_lot: Error: expiration_date is required
          - set_quantity: User clicked on the confirm button
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_lot(picking, selected_lines, message=message)
        if not selected_lines.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_lot(picking, selected_lines, message=message)
        lot_model = self.env["stock.production.lot"]
        search = self._actions_for("search")
        # TODO: Are we sure lot_name and expiry_date are mutually exclusive?
        if lot_name:
            for line in selected_lines:
                lot = search.lot_from_scan(
                    lot_name, products=selected_lines.mapped("product_id")
                )
                if not lot:
                    # TODO: We should collect all the values to create
                    # and create with a list instead.
                    # We could then map the lot to the line using the line id.
                    lot = lot_model.create(
                        {
                            "name": lot_name,
                            "product_id": line.product_id.id,
                            "company_id": self.env.company.id,
                            "use_expiration_date": line.product_id.use_expiration_date,
                        }
                    )
                line.lot_id = lot.id
                line._onchange_lot_id()
            return self._response_for_set_lot(picking, selected_lines)
        elif expiration_date:
            selected_lines.write({"expiration_date": expiration_date})
            selected_lines.mapped("lot_id").write({"expiration_date": expiration_date})
            return self._response_for_set_lot(picking, selected_lines)
        return self._response_for_set_lot(picking, selected_lines)

    def set_lot_confirm_action(self, picking_id, selected_line_ids):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        message = self._check_expiry_date(picking)
        if message:
            return self._response_for_set_lot(picking, selected_lines, message=message)
        return self._response_for_set_quantity(picking, selected_lines)

    def _check_expiry_date(self, picking):
        for line in picking.move_line_ids:
            use_expiration_date = (
                line.product_id.use_expiration_date or line.lot_id.use_expiration_date
            )
            if use_expiration_date and not line.expiration_date:
                return self.msg_store.expiration_date_missing()

    def set_quantity(
        self,
        picking_id,
        selected_line_ids,
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
          - select_line: User clicked on back
          - set_lot: Barcode not found. Ask user to create one from barcode
          - set_lot: expiration_date has been set on the selected line
          - set_lot: lot_it has been set on the selected line
          - set_lot: Error: expiration_date is required
          - set_quantity: User clicked on the confirm button
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_quantity(
                picking, selected_lines, message=message
            )
        if not selected_lines.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_quantity(
                picking, selected_lines, message=message
            )
        if quantity:
            selected_lines.qty_done = quantity
            return self._response_for_set_quantity(picking, selected_lines)
        if barcode:
            handlers = [
                self._set_quantity__scan_product,
                self._set_quantity__scan_packaging,
                self._set_quantity__scan_package,
                self._set_quantity__scan_location,
            ]
            response = self._use_handlers(handlers, picking, selected_lines, barcode)
            if response:
                return response
            # Nothing found, ask user if we should create a new pack for the scanned
            # barcode
            if not confirmation:
                return self._response_for_set_quantity(
                    picking,
                    selected_lines,
                    message=self.msg_store.create_new_pack_ask_confirmation(barcode),
                )
            package = self.env["stock.quant.package"].create({"name": barcode})
            selected_lines.result_package_id = package
            return self._response_for_set_destination(picking, selected_lines)

    def process_with_existing_pack(self, picking_id, selected_line_ids):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        return self._response_for_select_dest_package(picking, selected_lines)

    def process_with_new_pack(self, picking_id, selected_line_ids):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        new_pack = self.env["stock.quant.package"].create({})
        selected_lines.result_package_id = new_pack
        return self._response_for_set_destination(picking, selected_lines)

    def process_without_pack(self, picking_id, selected_line_ids):
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        return self._response_for_set_destination(picking, selected_lines)

    def set_destination(
        self, picking_id, selected_line_ids, location_id, confirmation=False
    ):
        """Set the destination on the move line.

        input:
            location_id: The id of the location

        transitions:
          - set_destination: Warning: User scanned a child location of the picking type.
            Ask for confirmation
          - set_destination: Error: User tried to scan a non-valid location
          - select_line: User scanned a child location of the move's dest location
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_set_destination(
                picking, selected_lines, message=message
            )
        if not selected_lines.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_set_destination(
                picking, selected_lines, message=message
            )
        location = self.env["stock.location"].browse(location_id)
        move_dest_location = selected_lines.location_dest_id
        move_child_locations = self.env["stock.location"].search(
            [("id", "child_of", move_dest_location.id)]
        )
        pick_type_dest_location = picking.picking_type_id.default_location_dest_id
        pick_type_child_locations = self.env["stock.location"].search(
            [("id", "child_of", pick_type_dest_location.id)]
        )
        if location in move_child_locations:
            # If location is a child of move's dest lcoation, assign it without asking
            selected_lines.location_dest_id = location
            return self._response_for_select_line(picking)
        elif location in pick_type_child_locations:
            # If location is a child of picking types's dest lcoation,
            # ask for confirmation before assigning
            if not confirmation:
                return self._response_for_set_destination(
                    picking,
                    selected_lines,
                    message=self.msg_store.place_in_location_ask_confirmation(
                        location.name
                    ),
                )
            selected_lines.location_dest_id = location
            return self._response_for_select_line(picking)
        # Otherwise, return an error
        return self._response_for_set_destination(
            picking, selected_lines, message=self.msg_store.dest_location_not_allowed()
        )

    def select_dest_package(
        self, picking_id, selected_line_ids, barcode, confirmation=False
    ):
        """Select the destination package for the move line

        Input:
            barcode: The barcode of the package

        transitions:
          - set_lot: User scanned a valid package
          - select_dest_package: Warning: User scanned an unknown barcode.
            Confirm to create one.
          - select_dest_package: Error: User scanned a non-empty package
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_lines = self.env["stock.move.line"].browse(selected_line_ids)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_dest_package(
                picking, selected_lines, message=message
            )
        if not selected_lines.exists():
            message = self.msg_store.record_not_found()
            return self._response_for_select_dest_package(
                picking, selected_lines, message=message
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
                    selected_lines,
                    message=self.msg_store.package_not_empty(package),
                )
            selected_lines.result_package_id = package
            return self._response_for_set_lot(picking, selected_lines)
        message = self.msg_store.create_new_pack_ask_confirmation(barcode)
        return self._response_for_select_dest_package(
            picking, selected_lines, message=message
        )


class ShopfloorReceptionValidator(Component):
    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.reception.validator"
    _usage = "reception.validator"

    def start(self):
        return {}

    def scan_document(self):
        return {"barcode": {"required": True, "type": "string"}}

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_lot(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "lot_name": {"type": "string"},
            "expiration_date": {"type": "string"},
        }

    def set_quantity(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "quantity": {"type": "float"},
            "barcode": {"type": "string"},
            "confirmation": {"type": "boolean"},
        }

    def process_with_existing_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def process_with_new_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def process_without_pack(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def set_destination(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean"},
        }

    def select_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
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
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
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
            "select_line": self._schema_select_line,
            "set_lot": self._schema_set_lot,
            "set_quantity": self._schema_set_quantity,
            "set_destination": self._schema_set_destination,
            "select_dest_package": self._schema_select_dest_package,
        }

    def _start_next_states(self):
        return {"select_document"}

    def _scan_document_next_states(self):
        return {"select_document", "select_line", "set_lot", "set_quantity"}

    def _scan_line_next_states(self):
        return {"select_line", "set_lot", "set_quantity"}

    def _set_lot_next_states(self):
        return {"select_line", "set_lot", "set_quantity"}

    def _set_quantity_next_states(self):
        return {"set_quantity", "select_line", "set_destination"}

    def _set_destination_next_states(self):
        return {"set_destination", "select_line"}

    def _select_dest_package_next_states(self):
        return {"set_lot", "select_dest_package"}

    def _done_next_states(self):
        return {"select_document", "select_line"}

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
                self._schema_stock_picking(), required=True
            )
        }

    def _schema_stock_picking(self, lines_with_packaging=False):
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": self.schemas._schema_list_of(
                    self.schemas.move_line(with_packaging=lines_with_packaging)
                )
            }
        )
        return schema

    @property
    def _schema_select_line(self):
        return {
            "picking": self.schemas._schema_dict_of(
                self._schema_stock_picking(), required=True
            )
        }

    @property
    def _schema_set_lot(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
        }

    @property
    def _schema_set_quantity(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_set_destination(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_select_dest_package(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    # ENDPOINTS

    def start(self):
        return self._response_schema(next_states=self._start_next_states())

    def scan_document(self):
        return self._response_schema(next_states=self._scan_document_next_states())

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
