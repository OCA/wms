# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
import collections

from odoo import fields

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component


class DeliveryShipment(Component):
    """Methods for the Delivery with Shipment Advices process

    Deliver the goods by processing the PACK and raw products by delivery order
    into a shipment advice.

    Multiple operators could be processing a same delivery order.

    You will find a sequence diagram describing states and endpoints
    relationships [here](../docs/delivery_shipment_diag_seq.png).
    Keep [the sequence diagram](../docs/delivery_shipment_diag_seq.plantuml)
    up-to-date if you change endpoints.

    Three cases:

    * Manager assign shipment advice to loading dock, plan its content and start them
    * Manager assign shipment advice to loading dock without content planning and start them
    * Operators create shipment advice on the fly (option “Allow shipment advice creation”
      in the scenario)

    Expected:

    * Existing packages are moved to customer location
    * Products are moved to customer location as raw products
    * Bin packed products are placed in new shipping package and shipped to customer
    * A shipment advice is marked as done
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.delivery.shipment"
    _usage = "delivery_shipment"
    _description = __doc__

    def scan_dock(self, barcode, confirmation=False):
        """Scan a loading dock.

        Called at the beginning of the workflow to select the shipment advice
        (corresponding to the scanned loading dock) to work on.

        If no shipment advice in progress related to the scanned loading dock
        is found, a new one is created if the menu as the option
        "Allow to create shipment advice" enabled.

        Transitions:
        * scan_document: a shipment advice has been found or created (with or
          without planned moves)
        * scan_dock: no shipment advice found
        """
        if not barcode:
            # End point called with the back button
            return self._response_for_scan_dock()
        search = self._actions_for("search")
        dock = search.dock_from_scan(barcode)
        if dock:
            shipment_advice = self._find_shipment_advice_from_dock(dock)
            if not shipment_advice:
                if not self.work.menu.allow_shipment_advice_create:
                    return self._response_for_scan_dock(
                        message=self.msg_store.no_shipment_in_progress()
                    )
                if not confirmation:
                    return self._response_for_scan_dock(
                        message=self.msg_store.scan_dock_again_to_confirm(dock),
                        confirmation_required=barcode,
                    )
                if confirmation != barcode:
                    return self._response_for_scan_dock(
                        message=self.msg_store.scan_dock_again_to_confirm(dock),
                        confirmation_required=barcode,
                    )
                shipment_advice = self._create_shipment_advice_from_dock(dock)
            return self._response_for_scan_document(shipment_advice)
        return self._response_for_scan_dock(message=self.msg_store.barcode_not_found())

    def scan_document(
        self, shipment_advice_id, barcode, picking_id=None, location_id=None
    ):
        """Scan an operation or location; a package, a product or a lot.

        If an operation or a location is scanned, reload the screen with the related planned
        content or full content of this operation/location for this shipment advice.

        If a package, a product or a lot is scanned, it will be loaded in the
        current shipment advice and the screen will be reloaded with the related
        current location or operation listing its planned or full content.

        If all the planned content (if any) has been loaded, redirect the user
        to the next state 'loading_list'.

        Transitions:
        * scan_document: once a good is loaded, or a operation has been
          scanned, or in case of error
        * loading_list: all planned content (if any) have been processed
        * scan_dock: error (shipment not found...)
        """
        shipment_advice = (
            self.env["shipment.advice"].browse(shipment_advice_id).exists()
        )
        if not shipment_advice:
            return self._response_for_scan_dock(
                message=self.msg_store.record_not_found()
            )
        picking = None
        if picking_id:
            picking = self.env["stock.picking"].browse(picking_id).exists()
            if not picking:
                return self._response_for_scan_document(
                    shipment_advice, message=self.msg_store.stock_picking_not_found()
                )
            message = self._check_picking_status(picking, shipment_advice)
            if message:
                return self._response_for_scan_document(
                    shipment_advice, message=message
                )
        location = None
        if location_id:
            # Filtering location the user is working from.
            location = self.env["stock.location"].browse(location_id).exists()
        if not barcode:
            # End point called with the back button
            return self._response_for_scan_document(shipment_advice, picking, location)
        search = self._actions_for("search")
        # Look for a location
        scanned_location = search.location_from_scan(barcode)
        if scanned_location:
            return self._scan_location(shipment_advice, scanned_location)
        # Look for an operation
        scanned_picking = search.picking_from_scan(barcode)
        if scanned_picking:
            return self._scan_picking(shipment_advice, scanned_picking)
        # Look for a package
        scanned_package = search.package_from_scan(barcode)
        if scanned_package:
            return self._scan_package(
                shipment_advice, scanned_package, picking, location
            )
        # Look for a lot (restricted to the relevant products as a lot number
        # can be shared by different products)
        move_lines = self.env["stock.move.line"].search(
            self._find_move_lines_domain(shipment_advice)
        )
        scanned_lot = search.lot_from_scan(barcode, products=move_lines.product_id)
        if scanned_lot:
            return self._scan_lot(shipment_advice, scanned_lot, picking, location)
        scanned_product = search.product_from_scan(barcode)
        if not scanned_product:
            packaging = search.packaging_from_scan(barcode)
            scanned_product = packaging.product_id
        if scanned_product:
            return self._scan_product(
                shipment_advice, scanned_product, picking, location
            )
        return self._response_for_scan_document(
            shipment_advice,
            picking,
            location=location,
            message=self.msg_store.barcode_not_found(),
        )

    def _scan_location(self, shipment_advice, location):
        """Return the planned or available content of the scanned location."""
        if not self.is_src_location_valid(location):
            message = self.msg_store.location_not_allowed()
            return self._response_for_scan_document(shipment_advice, message=message)
        return self._response_for_scan_document(shipment_advice, location=location)

    def _scan_picking(self, shipment_advice, picking):
        """Return the planned or available content of the scanned delivery for
        the current shipment advice.

        If the shipment advice had planned content and that the scanned delivery
        is not part of it, returns an error message.
        """
        message = self._check_picking_status(picking, shipment_advice)
        if message:
            return self._response_for_scan_document(shipment_advice, message=message)
        else:
            # Check that the delivery has available and not loaded content to load
            move_lines_to_process = self._find_move_lines_to_process_from_picking(
                shipment_advice, picking
            )
            if not move_lines_to_process:
                return self._response_for_scan_document(
                    shipment_advice,
                    message=self.msg_store.no_delivery_content_to_load(picking),
                )
        return self._response_for_scan_document(shipment_advice, picking)

    def _scan_package(self, shipment_advice, package, picking, location):
        """Load the package in the shipment advice.

        Find the package level or move line (of the planned shipment advice in
        priority if any) corresponding to the scanned package and load it.
        If no content is found an error will be returned.
        """
        move_lines = self._find_move_lines_from_package(
            shipment_advice, package, picking, location
        )
        if move_lines:
            # Check transfer status
            message = self._check_picking_status(move_lines.picking_id, shipment_advice)
            if message:
                return self._response_for_scan_document(
                    shipment_advice,
                    location=location,
                    message=message,
                )
            # Check that the product isn't already loaded
            package_level = move_lines.package_level_id
            if package_level._is_loaded_in_shipment():
                return self._response_for_scan_document(
                    shipment_advice,
                    move_lines.picking_id,
                    location=location,
                    message=self.msg_store.package_already_loaded_in_shipment(
                        package, shipment_advice
                    ),
                )
            # Load the package
            package_level._load_in_shipment(shipment_advice)
            return self._response_for_scan_document_or_loading_list(
                shipment_advice,
                move_lines.picking_id,
                location=location,
            )
        message = None
        if location:
            message = self.msg_store.package_not_found_in_location(package, location)
        elif picking:
            message = self.msg_store.package_not_found_in_picking(package, picking)
        elif shipment_advice.planned_move_ids:
            message = self.msg_store.package_not_planned_in_shipment(
                package, shipment_advice
            )
        else:
            message = self.msg_store.unable_to_load_package_in_shipment(
                package, shipment_advice
            )
        return self._response_for_scan_document(
            shipment_advice, picking, location, message
        )

    def _scan_lot(self, shipment_advice, lot, picking, location):
        """Load the lot in the shipment advice.

        Find the first move line (of the planned shipment advice in
        priority if any) corresponding to the scanned lot and load it.
        If no move line is found an error will be returned.
        """
        move_lines = self._find_move_lines_from_lot(
            shipment_advice, lot, picking, location
        )
        if move_lines:
            # Check transfer status
            message = self._check_picking_status(move_lines.picking_id, shipment_advice)
            if message:
                return self._response_for_scan_document(
                    shipment_advice, location=location, message=message
                )
            # Check that the lot doesn't belong to a package
            package_levels_not_loaded = move_lines.package_level_id.filtered(
                lambda pl: not pl.is_done
            )
            if package_levels_not_loaded:
                return self._response_for_scan_document(
                    shipment_advice,
                    move_lines.picking_id,
                    message=self.msg_store.lot_owned_by_packages(
                        package_levels_not_loaded.package_id
                    ),
                    location=location,
                )
            # Check that the lot isn't already loaded
            if move_lines._is_loaded_in_shipment():
                return self._response_for_scan_document(
                    shipment_advice,
                    move_lines.picking_id,
                    message=self.msg_store.lot_already_loaded_in_shipment(
                        lot, shipment_advice
                    ),
                    location=location,
                )
            # Load the lot
            move_lines._load_in_shipment(shipment_advice)
            return self._response_for_scan_document_or_loading_list(
                shipment_advice, move_lines.picking_id, location=location
            )
        message = None
        if location:
            message = self.msg_store.lot_not_found_in_location(lot, location)
        elif picking:
            message = self.msg_store.lot_not_found_in_picking(lot, picking)
        elif shipment_advice.planned_move_ids:
            message = self.msg_store.lot_not_planned_in_shipment(lot, shipment_advice)
        else:
            message = self.msg_store.unable_to_load_lot_in_shipment(
                lot, shipment_advice
            )
        return self._response_for_scan_document(
            shipment_advice, picking, location, message
        )

    def _scan_product(self, shipment_advice, product, picking, location):
        """Load the product in the shipment advice.

        Find the first move line (of the planned shipment advice in
        priority if any) corresponding to the scanned product and load it.
        If no move line is found an error will be returned.
        """
        if not picking:
            return self._response_for_scan_document(
                shipment_advice,
                message=self.msg_store.scan_operation_first(),
            )
        move_lines = self._find_move_lines_from_product(
            shipment_advice, product, picking, location
        )
        if move_lines:
            # Check transfer status
            message = self._check_picking_status(move_lines.picking_id, shipment_advice)
            if message:
                return self._response_for_scan_document(
                    shipment_advice, message=message
                )
            # Check if product lines are linked to some packages
            # In this case we want to process the package as a whole
            package_levels_not_loaded = move_lines.package_level_id.filtered(
                lambda pl: not pl.is_done
            )
            if package_levels_not_loaded:
                return self._response_for_scan_document(
                    shipment_advice,
                    picking,
                    message=self.msg_store.product_owned_by_packages(
                        package_levels_not_loaded.package_id
                    ),
                )
            # Check if product lines are linked to a lot
            # If there are several lots corresponding to this product, we want
            # to scan a lot instead of a product
            if product.tracking != "none":
                lots_not_loaded = move_lines.filtered(
                    lambda ml: (
                        not ml.package_level_id
                        and ml.qty_done != ml.product_uom_qty
                        and ml.lot_id
                    )
                )
                if len(lots_not_loaded) > 1:
                    return self._response_for_scan_document(
                        shipment_advice,
                        picking,
                        message=self.msg_store.product_owned_by_lots(
                            lots_not_loaded.lot_id
                        ),
                    )
            # Check that the product isn't already loaded
            if move_lines._is_loaded_in_shipment():
                return self._response_for_scan_document(
                    shipment_advice,
                    picking,
                    message=self.msg_store.product_already_loaded_in_shipment(
                        product, shipment_advice
                    ),
                )
            # Load the lines
            move_lines._load_in_shipment(shipment_advice)
            return self._response_for_scan_document_or_loading_list(
                shipment_advice,
                move_lines.picking_id,
            )
        message = None
        if location:
            message = self.msg_store.product_not_found_in_location_or_transfer(
                product, location, picking
            )
        elif shipment_advice.planned_move_ids:
            message = self.msg_store.product_not_planned_in_shipment(
                product, shipment_advice
            )
        else:
            message = self.msg_store.unable_to_load_product_in_shipment(
                product, shipment_advice
            )
        return self._response_for_scan_document(
            shipment_advice, picking, location, message
        )

    def unload_move_line(self, shipment_advice_id, move_line_id, location_id=None):
        """Unload a move line from a shipment advice.

        Transitions:
        * scan_document: reload the screen once the move line is unloaded
        * scan_dock: error (record ID not found...)
        """
        shipment_advice = (
            self.env["shipment.advice"].browse(shipment_advice_id).exists()
        )
        move_line = self.env["stock.move.line"].browse(move_line_id).exists()
        if not shipment_advice or not move_line:
            return self._response_for_scan_dock(
                message=self.msg_store.record_not_found()
            )
        location = None
        if location_id:
            # Filtering location the user is working from.
            location = self.env["stock.location"].browse(location_id).exists()
        # Unload the move line
        move_line._unload_from_shipment()
        return self._response_for_scan_document(
            shipment_advice, move_line.picking_id, location=location
        )

    def unload_package_level(
        self, shipment_advice_id, package_level_id, location_id=None
    ):
        """Unload a package level from a shipment advice.

        Transitions:
        * scan_document: reload the screen once the package level is unloaded
        * scan_dock: error (record ID not found...)
        """
        shipment_advice = (
            self.env["shipment.advice"].browse(shipment_advice_id).exists()
        )
        package_level = (
            self.env["stock.package_level"].browse(package_level_id).exists()
        )
        if not shipment_advice or not package_level:
            return self._response_for_scan_dock(
                message=self.msg_store.record_not_found()
            )
        location = None
        if location_id:
            # Filtering location the user is working from.
            location = self.env["stock.location"].browse(location_id).exists()
        # Unload the package level
        package_level._unload_from_shipment()
        return self._response_for_scan_document(
            shipment_advice, package_level.picking_id, location=location
        )

    def loading_list(self, shipment_advice_id):
        """Redirect to the 'loading_list' state listing the loaded (with their
        loading progress) and not loaded deliveries for the given shipment.
        """
        shipment_advice = (
            self.env["shipment.advice"].browse(shipment_advice_id).exists()
        )
        if not shipment_advice:
            return self._response_for_scan_dock(
                message=self.msg_store.record_not_found()
            )
        return self._response_for_loading_list(shipment_advice)

    def validate(self, shipment_advice_id, confirmation=False):
        """Validate the shipment advice.

        When called the first time with `confirmation=False`, it returns a summary
        of the deliveries (loaded or that can still be loaded) for that shipment.
        """
        shipment_advice = (
            self.env["shipment.advice"].browse(shipment_advice_id).exists()
        )
        if not shipment_advice:
            return self._response_for_scan_dock(
                message=self.msg_store.record_not_found()
            )
        if not confirmation:
            return self._response_for_validate(shipment_advice)
        shipment_advice.action_done()
        return self._response_for_scan_dock(
            message=self.msg_store.shipment_validated(shipment_advice)
        )

    def _response_for_scan_dock(self, message=None, confirmation_required=None):
        """Transition to the 'scan_dock' state.

        The client screen invite the user to scan a dock to find or create an
        available shipment advice.

        If `confirmation_required` is set, the client will ask to scan again
        the dock to create a shipment advice.
        """
        data = {"confirmation_required": confirmation_required}
        return self._response(next_state="scan_dock", data=data, message=message)

    def _response_for_scan_document(
        self, shipment_advice, picking=None, location=None, message=None
    ):
        data = {
            "shipment_advice": self.data.shipment_advice(shipment_advice),
        }
        # The filter on location takes priority on the picking filter
        if location:
            data.update(
                location=self.data.location(location),
                content=self._data_for_content_to_load_from_picking(
                    shipment_advice, location=location
                ),
            )
        elif picking:
            data.update(
                picking=self.data.picking(picking),
                content=self._data_for_content_to_load_from_picking(
                    shipment_advice, picking
                ),
            )
        else:
            data.update(
                content=self._data_for_content_to_load_from_pickings(shipment_advice),
            )
        return self._response(next_state="scan_document", data=data, message=message)

    def _response_for_loading_list(self, shipment_advice, message=None):
        data = {
            "shipment_advice": self.data.shipment_advice(shipment_advice),
            "lading": self._data_for_lading(shipment_advice),
            "on_dock": self._data_for_on_dock(shipment_advice),
        }
        return self._response(next_state="loading_list", data=data, message=message)

    def _response_for_scan_document_or_loading_list(
        self, shipment_advice, picking, message=None, location=None
    ):
        """Route on 'scan_document' or 'loading_list' states.

        If all planned moves of the shipment are loaded, route to 'loading_list',
        state otherwise redirect to 'scan_document'.
        """
        planned_moves = shipment_advice.planned_move_ids
        loaded_move_lines = shipment_advice.loaded_move_line_ids
        if planned_moves and planned_moves.move_line_ids == loaded_move_lines:
            return self._response_for_loading_list(
                shipment_advice,
                message=self.msg_store.shipment_planned_content_fully_loaded(),
            )
        return self._response_for_scan_document(
            shipment_advice, picking, location=location, message=message
        )

    def _response_for_validate(self, shipment_advice, message=None):
        data = {
            "shipment_advice": self.data.shipment_advice(shipment_advice),
            "lading": self._data_for_lading_summary(shipment_advice),
            "on_dock": self._data_for_on_dock_summary(shipment_advice),
        }
        return self._response(next_state="validate", data=data, message=message)

    def _data_for_content_to_load_from_pickings(self, shipment_advice):
        """Return goods to load from transfers partially loaded in a shipment.

        It returns a dict where keys are source locations and values are
        dictionaries listing package_levels and move_lines that remain to load
        from transfers partially loaded in a shipment.
        """
        domain = self._find_move_lines_domain(shipment_advice)
        # Restrict to lines not loaded
        domain.insert(0, ("shipment_advice_id", "=", False))
        # Find lines to load from partially loaded transfers if the shipment
        # is not planned.
        if not shipment_advice.planned_move_ids:
            all_lines_to_load = self.env["stock.move.line"].search(domain)
            all_pickings = all_lines_to_load.picking_id
            loaded_lines = self.env["stock.move.line"].search(
                [
                    ("picking_id", "in", all_pickings.ids),
                    ("id", "not in", all_lines_to_load.ids),
                    ("shipment_advice_id", "!=", False),
                ]
            )
            pickings_partially_loaded = loaded_lines.picking_id
            domain += [("picking_id", "in", pickings_partially_loaded.ids)]
        move_lines = self.env["stock.move.line"].search(domain)
        return self._prepare_data_for_content(move_lines, group_by_sale=False)

    def _data_for_content_to_load_from_picking(
        self, shipment_advice, picking=None, location=None
    ):
        """Return a dictionary where keys are source locations
        and values are dictionaries listing package_levels and move_lines
        loaded or to load.
        """
        # Grab move lines to sort, restricted to the current delivery
        if picking:
            move_lines = self._find_move_lines_to_process_from_picking(
                shipment_advice, picking
            )
        elif location:
            move_lines = self._find_move_lines_from_location(shipment_advice, location)
        group_by_sale = bool(location)
        return self._prepare_data_for_content(move_lines, group_by_sale=group_by_sale)

    def _prepare_data_for_content(self, move_lines, group_by_sale=False):
        """Returns data for package levels and/or move lines.

        The data is grouped by source location with a key for package levels and
        a key for move lines.
        The package levels can be grouped by related sales order and if they are not
        they will be all stored into a key whose name is only spaces.
        The move lines are not grouped by sales.

        E.g:
            {
                "SRC_LOCATION1": {
                    "package_levels": {
                       "sale 01": [{PKG_LEVEL_DATA}, ...],
                       "sale 02": [{PKG_LEVEL_DATA}, ...],
                       " ": [{PKG_LEVEL_DATA}, ...],
                    }
                    "move_lines": [{MOVE_LINE_DATA}, ...],
                },
                "SRC_LOCATION2": {
                    ...
                },
            }
        """
        empty_group_name = "null"
        data = collections.OrderedDict()
        package_level_ids = []

        # Sort and group move lines by source location and prepare the data
        sales_started = []
        if group_by_sale:
            sales_started = move_lines.shipment_advice_id.loaded_picking_ids.sale_id
            # Grouping by sales (the packages) sort starting from last position
            #  2 the lines NOT in a sales order whose loading has started.
            #  1 the lines in a sales being loaded and the line is done.
            #  0 the lines in a sales being loaded and not yet done
            move_lines = move_lines.sorted(
                lambda ml: 2
                if ml.move_id.sale_line_id.order_id not in sales_started
                else (1 if ml.package_level_id.is_done else 0)
            )
        else:
            move_lines = move_lines.sorted(lambda ml: ml.location_id.name)

        for move_line in move_lines:
            location_data = data.setdefault(move_line.location_id.name, {})
            if move_line.package_level_id:
                pl_data = location_data.setdefault(
                    "package_levels", collections.OrderedDict()
                )
                if move_line.package_level_id.id in package_level_ids:
                    continue
                if group_by_sale:
                    group_name = (
                        move_line.move_id.sale_line_id.order_id.name or empty_group_name
                    )
                else:
                    group_name = empty_group_name
                pl_group_data = pl_data.setdefault(group_name, [])
                pl_group_data.append(
                    self.data.package_level(move_line.package_level_id)
                )
                package_level_ids.append(move_line.package_level_id.id)
            else:
                location_data.setdefault("move_lines", []).append(
                    self.data.move_line(move_line)
                )
        return data

    def _data_for_lading(self, shipment_advice):
        """Return a list of deliveries loaded in the shipment advice.

        The deliveries could be partially or fully loaded. For each of them a %
        of content loaded is computed (either based on bulk content or packages).
        """
        pickings = shipment_advice.loaded_picking_ids.filtered(
            lambda p: p.picking_type_id & self.picking_types
        ).sorted("loaded_progress_f")
        return self.data.pickings_loaded(pickings)

    def _data_for_lading_summary(self, shipment_advice):
        """Return the number of deliveries/packages/bulk lines loaded."""
        pickings = shipment_advice.loaded_picking_ids.filtered(
            lambda p: p.picking_type_id & self.picking_types
        ).sorted("loaded_progress_f")
        return {
            "loaded_pickings_count": len(pickings),
            "loaded_packages_count": sum(pickings.mapped("loaded_packages_count")),
            "total_packages_count": sum(pickings.mapped("total_packages_count")),
            "loaded_bulk_lines_count": sum(pickings.mapped("loaded_move_lines_count")),
            "total_bulk_lines_count": sum(pickings.mapped("total_move_lines_count")),
            "loaded_weight": sum(pickings.mapped("loaded_weight")),
        }

    def _data_for_on_dock(self, shipment_advice):
        """Return a list of deliveries not loaded in the shipment advice.

        The deliveries are not loaded at all in the shipment.
        """
        return self.data.pickings(
            self._find_pickings_not_loaded_from_shipment(shipment_advice)
        )

    def _data_for_on_dock_summary(self, shipment_advice):
        """Return the number of deliveries/packages/bulk lines not loaded."""
        pickings = self._find_pickings_not_loaded_from_shipment(shipment_advice)
        return {
            "total_pickings_count": len(pickings),
            "total_packages_count": sum(pickings.mapped("total_packages_count")),
            "total_bulk_lines_count": sum(pickings.mapped("total_move_lines_count")),
        }

    def _find_shipment_advice_from_dock_domain(self, dock):
        return [
            ("dock_id", "=", dock.id),
            ("state", "in", ["in_progress"]),
            ("warehouse_id", "in", self.picking_types.warehouse_id.ids),
        ]

    def _find_shipment_advice_from_dock(self, dock):
        return self.env["shipment.advice"].search(
            self._find_shipment_advice_from_dock_domain(dock),
            limit=1,
            order="arrival_date",
        )

    def _prepare_shipment_advice_from_dock_values(self, dock):
        return {
            "dock_id": dock.id,
            "arrival_date": fields.Datetime.to_string(fields.Datetime.now()),
            "warehouse_id": dock.warehouse_id.id,
        }

    def _create_shipment_advice_from_dock(self, dock):
        shipment_advice = self.env["shipment.advice"].create(
            self._prepare_shipment_advice_from_dock_values(dock)
        )
        shipment_advice.action_confirm()
        shipment_advice.action_in_progress()
        return shipment_advice

    def _find_move_lines_from_location(self, shipment_advice, location):
        """Returns the move line corresponding to `location` for the given shipment."""
        location.ensure_one()
        domain = self._find_move_lines_domain(shipment_advice)
        domain.append(("location_id", "child_of", location.id))
        return self.env["stock.move.line"].search(domain)

    def _find_move_lines_to_process_from_picking(self, shipment_advice, picking):
        """Returns the moves to load or unload for the given shipment and delivery.

        - if the shipment is planned, returns delivery content planned for
          this shipment
        - if the shipment is not planned, returns delivery content to
          load/unload (not planned and not loaded in another shipment)
        """
        picking.ensure_one()
        # Shipment with planned content
        if shipment_advice.planned_move_ids:
            # Restrict to delivery planned moves
            moves = (shipment_advice.planned_move_ids & picking.move_lines).filtered(
                lambda m: m.state in ("assigned", "partially_available")
            )
        # Shipment without planned content
        else:
            # Restrict to delivery moves not planned
            moves = picking.move_lines.filtered(lambda m: not m.shipment_advice_id)
        return moves.move_line_ids.filtered(
            lambda ml: not ml.shipment_advice_id
            or shipment_advice & ml.shipment_advice_id
        )

    def _find_move_lines_domain(self, shipment_advice):
        """Returns the base domain to look for move lines for a given shipment."""
        return shipment_advice._find_move_lines_domain(
            self.picking_types
        )  # Defined in `shipment_advice`

    def _find_move_lines_from_package(
        self, shipment_advice, package, picking, location
    ):
        """Returns the move line corresponding to `package` for the given shipment."""
        domain = self._find_move_lines_domain(shipment_advice)
        # FIXME should we check also result package here?
        domain.append(("package_id", "=", package.id))
        if location:
            domain.append(
                ("location_id", "child_of", location.id),
            )
        if picking:
            domain.append(
                ("picking_id", "=", picking.id),
            )
        return self.env["stock.move.line"].search(domain)

    def _find_move_lines_from_lot(self, shipment_advice, lot, picking, location):
        """Returns the move line corresponding to `lot` for the given shipment."""
        domain = self._find_move_lines_domain(shipment_advice)
        domain.append(("lot_id", "=", lot.id))
        if location:
            domain.append(
                ("location_id", "child_of", location.id),
            )
        if picking:
            domain.append(
                ("picking_id", "=", picking.id),
            )
        return self.env["stock.move.line"].search(domain)

    def _find_move_lines_from_product(
        self,
        shipment_advice,
        product,
        picking,
        location,
        in_package_not_loaded=False,
        in_lot=False,
    ):
        """Returns the move lines corresponding to `product` and `picking`
        for the given shipment.
        """
        domain = self._find_move_lines_domain(shipment_advice)
        domain.extend(
            [
                ("product_id", "=", product.id),
                ("picking_id", "=", picking.id),
            ]
        )
        if location:
            domain.append(
                ("location_id", "child_of", location.id),
            )
        if in_package_not_loaded:
            domain.append(
                ("package_level_id", "!=", False),
                ("package_level_id.is_done", "=", False),
            )
        if in_lot:
            domain.append(("lot_id", "!=", False))
        return self.env["stock.move.line"].search(domain)

    def _find_move_lines_not_loaded_from_shipment(self, shipment_advice):
        """Returns the move lines not loaded at all from the shipment advice."""
        domain = self._find_move_lines_domain(shipment_advice)
        domain.append(("qty_done", "=", 0))
        return self.env["stock.move.line"].search(domain)

    def _find_pickings_not_loaded_from_shipment(self, shipment_advice):
        """Returns the deliveries that are not loaded for the given shipment."""
        pickings_loaded = shipment_advice.loaded_picking_ids.filtered(
            lambda p: p.picking_type_id & self.picking_types
        )
        # Shipment with planned content
        if shipment_advice.planned_move_ids:
            pickings_planned = shipment_advice.planned_picking_ids.filtered(
                lambda p: p.picking_type_id & self.picking_types
            )
            pickings_not_loaded = pickings_planned - pickings_loaded
        # Shipment without planned content
        else:
            # Deliveries not loaded have all their move lines not loaded at all
            # (even partially)
            move_lines_not_loaded = self._find_move_lines_not_loaded_from_shipment(
                shipment_advice
            )
            pickings_not_loaded = (
                move_lines_not_loaded.picking_id - shipment_advice.loaded_picking_ids
            )
        return pickings_not_loaded

    def _check_picking_status(self, pickings, shipment_advice):
        # Overloaded to add checks against a shipment advice
        message = super()._check_picking_status(pickings)
        if message:
            return message
        for picking in pickings:
            # Shipment with planned content
            if shipment_advice.planned_move_ids:
                if picking not in shipment_advice.planned_picking_ids:
                    return self.msg_store.picking_not_planned_in_shipment(
                        picking, shipment_advice
                    )
            # Check carrier's provider compatibility between shipment and picking
            carriers = shipment_advice.carrier_ids
            shipment_carrier_types = set(carriers.mapped("delivery_type"))
            picking_carrier_type = {picking.carrier_id.delivery_type}
            if carriers and not shipment_carrier_types & picking_carrier_type:
                return self.msg_store.carrier_not_allowed_by_shipment(picking)


class ShopfloorDeliveryShipmentValidator(Component):
    """Validators for the Delivery with Shipment Advices endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.delivery.shipment.validator"
    _usage = "delivery_shipment.validator"

    def scan_dock(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "confirmation": {
                "required": False,
                "nullable": True,
                "type": "string",
            },
        }

    def scan_document(self):
        return {
            "shipment_advice_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "barcode": {"required": True, "type": "string"},
            "picking_id": {
                "coerce": to_int,
                "required": False,
                "nullable": True,
                "type": "integer",
            },
            "location_id": {
                "coerce": to_int,
                "required": False,
                "nullable": True,
                "type": "integer",
            },
        }

    def unload_move_line(self):
        return {
            "shipment_advice_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {
                "coerce": to_int,
                "required": False,
                "nullable": True,
                "type": "integer",
            },
        }

    def unload_package_level(self):
        return {
            "shipment_advice_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "package_level_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "location_id": {
                "coerce": to_int,
                "required": False,
                "nullable": True,
                "type": "integer",
            },
        }

    def loading_list(self):
        return {
            "shipment_advice_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }

    def validate(self):
        return {
            "shipment_advice_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "confirmation": {
                "coerce": to_bool,
                "required": False,
                "nullable": True,
                "type": "boolean",
            },
        }


class ShopfloorDeliveryShipmentValidatorResponse(Component):
    """Validators for the Delivery with Shipment Advices endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.delivery.shipment.validator.response"
    _usage = "delivery_shipment.validator.response"

    _start_state = "scan_dock"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "scan_dock": self._schema_scan_dock,
            "scan_document": self._schema_scan_document,
            "loading_list": self._schema_loading_list,
            "validate": self._schema_validate,
        }

    @property
    def _schema_scan_dock(self):
        return {
            "confirmation_required": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
        }

    @property
    def _schema_scan_document(self):
        shipment_schema = self.schemas.shipment_advice()
        picking_schema = self.schemas.picking()
        location_schema = self.schemas.location()
        return {
            "shipment_advice": {
                "type": "dict",
                "nullable": False,
                "schema": shipment_schema,
            },
            "picking": {"type": "dict", "nullable": True, "schema": picking_schema},
            "content": {
                "type": "dict",
                "nullable": True,
                # TODO
                # "schema": shipment_schema,
            },
            "location": {"type": "dict", "nullable": True, "schema": location_schema},
        }

    @property
    def _schema_loading_list(self):
        shipment_schema = self.schemas.shipment_advice()
        picking_loaded_schema = self.schemas.picking_loaded()
        picking_schema = self.schemas.picking()
        return {
            "shipment_advice": self.schemas._schema_dict_of(shipment_schema),
            "lading": self.schemas._schema_list_of(picking_loaded_schema),
            "on_dock": self.schemas._schema_list_of(picking_schema),
        }

    @property
    def _schema_validate(self):
        shipment_schema = self.schemas.shipment_advice()
        shipment_lading_summary_schema = self.schemas.shipment_lading_summary()
        shipment_on_dock_summary_schema = self.schemas.shipment_on_dock_summary()
        return {
            "shipment_advice": {
                "type": "dict",
                "nullable": False,
                "schema": shipment_schema,
            },
            "lading": self.schemas._schema_dict_of(shipment_lading_summary_schema),
            "on_dock": self.schemas._schema_dict_of(shipment_on_dock_summary_schema),
        }

    def scan_dock(self):
        return self._response_schema(next_states={"scan_document", "scan_dock"})

    def scan_document(self):
        return self._response_schema(
            next_states={"scan_document", "scan_dock", "loading_list"}
        )

    def loading_list(self):
        return self._response_schema(next_states={"loading_list", "scan_dock"})

    def validate(self):
        return self._response_schema(next_states={"validate", "scan_dock"})
