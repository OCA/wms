from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

# NOTE: we need to know if the destination package is set, but sometimes
# the dest. package is kept, so we will use field shopfloor_checkout_packed
# on the move line


class Checkout(Component):
    """
    Methods for the Checkout Process

    This process runs on existing moves.
    It happens on the "Packing" step of a pick/pack/ship.

    Use cases:

    1) Products are packed (e.g. full pallet shipping) and we keep the packages
    2) Products are packed (e.g. rollercage bins) and we create a new package
       with same content for shipping
    3) Products are packed (e.g. half-pallet ) and we merge several into one
    4) Products are packed (e.g. too high pallet) and we split it on several
    5) Products are not packed (e.g. raw products) and we create new packages
    6) Products are not packed (e.g. raw products) and we do not create packages

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.checkout"
    _usage = "checkout"
    _description = __doc__

    def scan_document(self, barcode):
        """Scan a package, a stock.picking or a location

        When a location is scanned, if all the move lines from this destination
        are for the same stock.picking, the stock.picking is used for the
        next steps.

        When a package is scanned, if the package has a move line to move it
        from a location/sublocation of the current stock.picking.type, the
        stock.picking for the package is used for the next steps.

        When a stock.picking is scanned, it is used for the next steps.

        In every case above, the stock.picking must be entirely available and
        must match the current picking type.

        Transitions:
        * select_document: when no stock.picking could be found
        * select_line: a stock.picking is selected
        * summary: stock.picking is selected and all its lines have a
          destination pack set
        """
        search = self.actions_for("search")
        picking = search.stock_picking_from_scan(barcode)
        if not picking:
            location = search.location_from_scan(barcode)
            if location:
                if not location.is_sublocation_of(
                    self.picking_type.default_location_src_id
                ):
                    return self._response_for_scan_location_not_allowed()
                lines = location.source_move_line_ids
                pickings = lines.mapped("picking_id")
                if len(pickings) == 1:
                    picking = pickings
                else:
                    return self._response_for_several_stock_picking_found()
        if not picking:
            package = search.package_from_scan(barcode)
            if package:
                lines = package.planned_move_line_ids
                pickings = lines.mapped("picking_id")
                if len(pickings) == 1:
                    picking = pickings
        return self._select_picking(picking, "select_document")

    def _select_picking(self, picking, state_for_error):
        message = self.actions_for("message")
        if not picking:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=message.stock_picking_not_found()
                )
            return self._response_for_barcode_no_stock_picking_found()
        if picking.picking_type_id != self.picking_type:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=message.cannot_move_something_in_picking_type()
                )
            return self._response_for_scan_picking_type_not_allowed()
        if picking.state != "assigned":
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=message.stock_picking_not_available(picking)
                )
            return self._response_for_picking_not_assigned(picking)
        # TODO if all lines have a dest package set, go to summary
        return self._response_for_selected_stock_picking(picking)

    def _response_for_selected_stock_picking(self, picking, message=None):
        return self._response(
            next_state="select_line",
            data={"picking": self._data_for_stock_picking(picking)},
            message=message,
        )

    def _response_for_picking_not_assigned(self, picking):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document",
            message=message.stock_picking_not_available(picking),
        )

    def _response_for_several_stock_picking_found(self):
        return self._response(
            next_state="select_document",
            message={
                "message_type": "error",
                "message": _(
                    "Several transfers found, please scan a package"
                    " or select a transfer manually."
                ),
            },
        )

    def _response_for_scan_picking_type_not_allowed(self):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document",
            message=message.cannot_move_something_in_picking_type(),
        )

    def _response_for_scan_location_not_allowed(self):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document", message=message.location_not_allowed()
        )

    def _response_for_barcode_no_stock_picking_found(self):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document", message=message.barcode_not_found()
        )

    def _response_for_stock_picking_has_been_deleted(self):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document", message=message.stock_picking_not_found()
        )

    def _data_for_move_line(self, move_line):
        return {
            "id": move_line.id,
            "qty_done": move_line.qty_done,
            "quantity": move_line.product_uom_qty,
            "product": {
                "id": move_line.product_id.id,
                "name": move_line.product_id.name,
                "display_name": move_line.product_id.display_name,
                "default_code": move_line.product_id.default_code or "",
            },
            "lot": {"id": move_line.lot_id.id, "name": move_line.lot_id.name}
            if move_line.lot_id
            else None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                # TODO
                "weight": 0,
                # TODO
                "line_count": 0,
                "package_type_name": (
                    move_line.package_id.package_storage_type_id.name or ""
                ),
            }
            if move_line.package_id
            else None,
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                # TODO
                "weight": 0,
                # TODO
                "line_count": 0,
                "package_type_name": (
                    move_line.result_package_id.package_storage_type_id.name or ""
                ),
            }
            if move_line.result_package_id
            else None,
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "location_dest": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
        }

    def _data_for_stock_picking(self, picking):
        data = self._data_picking_base(picking)
        data.update(
            {
                "move_lines": [
                    self._data_for_move_line(ml) for ml in self._lines_to_pack(picking)
                ]
            }
        )
        return data

    def _lines_to_pack(self, picking):
        return picking.move_line_ids.filtered(
            lambda l: l.qty_done == 0 and not l.shopfloor_checkout_packed
        )

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "=", self.picking_type.id),
        ]

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"

    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_manual_selection()

    def _response_for_manual_selection(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        data = {"pickings": [self._data_picking_base(picking) for picking in pickings]}
        return self._response(next_state="manual_selection", data=data, message=message)

    def _data_picking_base(self, picking):
        return {
            "id": picking.id,
            "name": picking.name,
            "origin": picking.origin or "",
            "note": picking.note or "",
            "line_count": len(picking.move_line_ids),
            "partner": {"id": picking.partner_id.id, "name": picking.partner_id.name}
            if picking.partner_id
            else None,
        }

    def select(self, picking_id):
        """Select a stock picking for the process

        Used from the list of stock pickings (manual_selection), from there,
        the user can click on a stock.picking record which calls this method.

        The ``list_stock_picking`` returns only the valid records (same picking
        type, fully available, ...), but this method has to check again in case
        something changed since the list was sent to the client.

        Transitions:
        * manual_selection: stock.picking could finally not be selected (not
          available, ...)
        * summary: goes straight to this state used to set the moves as done when
          all the move lines with a reserved quantity have a 'quantity done'
        * select_line: the "normal" case, when the user has to put in pack/move
          lines
        """
        picking = self.env["stock.picking"].browse(picking_id).exists()
        return self._select_picking(picking, "manual_selection")

    def _response_for_select_package(self, lines, message=None):
        picking = lines.mapped("picking_id")
        return self._response(
            next_state="select_package",
            data={
                "selected_move_lines": [
                    self._data_for_move_line(line) for line in lines
                ],
                "picking": self._data_picking_base(picking),
            },
            message=message,
        )

    def _select_lines(self, lines):
        for line in lines:
            if line.shopfloor_checkout_packed:
                continue
            line.qty_done = line.product_uom_qty

        picking = lines.mapped("picking_id")
        other_lines = picking.move_line_ids - lines
        self._deselect_lines(other_lines)

    def _deselect_lines(self, lines):
        lines.filtered(lambda l: not l.shopfloor_checkout_packed).qty_done = 0

    def scan_line(self, picking_id, barcode):
        """Scan move lines of the stock picking

        It allows to select move lines of the stock picking for the next
        screen. Lines can be found either by scanning a package, a product or a
        lot.

        There should be no ambiguity, so for instance if a product is scanned but
        several packs contain it, the endpoint will ask to scan a pack; if the
        product is tracked by lot, to scan a lot.

        Once move lines are found, their ``qty_done`` is set to their reserved
        quantity.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_package: lines are selected, user is redirected to this
        screen to change the qty done and destination pack if needed
        """
        picking = self.env["stock.picking"].browse(picking_id)
        if not picking.exists():
            return self._response_stock_picking_does_not_exist()

        search = self.actions_for("search")
        message = self.actions_for("message")

        selection_lines = self._lines_to_pack(picking)
        # TODO handle no lines in selection go to summary

        package = search.package_from_scan(barcode)
        if package:
            return self._select_lines_from_package(picking, selection_lines, package)

        product = search.product_from_scan(barcode)
        if product:
            return self._select_lines_from_product(picking, selection_lines, product)

        lot = search.lot_from_scan(barcode)
        if lot:
            return self._select_lines_from_lot(picking, selection_lines, lot)

        return self._response_for_selected_stock_picking(
            picking, message=message.barcode_not_found()
        )

    def _select_lines_from_package(self, picking, selection_lines, package):
        lines = selection_lines.filtered(lambda l: l.package_id == package)
        if not lines:
            return self._response_for_selected_stock_picking(
                picking,
                message={
                    "message_type": "error",
                    "message": _("Package {} is not in the current transfer.").format(
                        package.name
                    ),
                },
            )
        self._select_lines(lines)
        return self._response_for_select_package(lines)

    def _select_lines_from_product(self, picking, selection_lines, product):
        message = self.actions_for("message")
        if product.tracking in ("lot", "serial"):
            return self._response_for_selected_stock_picking(
                picking, message=message.scan_lot_on_product_tracked_by_lot()
            )

        lines = selection_lines.filtered(lambda l: l.product_id == product)
        if not lines:
            return self._response_for_selected_stock_picking(
                picking,
                message={
                    "message_type": "error",
                    "message": _("Product is not in the current transfer."),
                },
            )

        # When products are as units outside of packages, we can select them for
        # packing, but if they are in a package, we want the user to scan the packages.
        # If the product is only in one package though, scanning the product selects
        # the package.
        packages = lines.mapped("package_id")
        # Do not use mapped here: we want to see if we have more than one package,
        # but also if we have one product as a package and the same product as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        if packages and len({l.package_id for l in lines}) > 1:
            return self._response_for_selected_stock_picking(
                picking, message=message.product_multiple_packages_scan_package()
            )
        elif packages:
            # Select all the lines of the package when we scan a product in a
            # package and we have only one.
            return self._select_lines_from_package(picking, selection_lines, packages)

        self._select_lines(lines)
        return self._response_for_select_package(lines)

    def _select_lines_from_lot(self, picking, selection_lines, lot):
        lines = selection_lines.filtered(lambda l: l.lot_id == lot)
        if not lines:
            return self._response_for_selected_stock_picking(
                picking,
                message={
                    "message_type": "error",
                    "message": _("Lot is not in the current transfer."),
                },
            )

        message = self.actions_for("message")
        # When lots are as units outside of packages, we can select them for
        # packing, but if they are in a package, we want the user to scan the packages.
        # If the product is only in one package though, scanning the lot selects
        # the package.
        packages = lines.mapped("package_id")
        # Do not use mapped here: we want to see if we have more than one
        # package, but also if we have one lot as a package and the same lot as
        # a unit in another line. In both cases, we want the user to scan the
        # package.
        if packages and len({l.package_id for l in lines}) > 1:
            return self._response_for_selected_stock_picking(
                picking, message=message.lot_multiple_packages_scan_package()
            )
        elif packages:
            # Select all the lines of the package when we scan a lot in a
            # package and we have only one.
            return self._select_lines_from_package(picking, selection_lines, packages)

        self._select_lines(lines)
        return self._response_for_select_package(lines)

    def select_line(self, picking_id, package_id=None, move_line_id=None):
        """Select move lines of the stock picking

        This is the same as ``scan_line``, except that a package id or a
        move_line_id is given by the client (user clicked on a list).

        It returns a list of move line ids that will be displayed by the
        screen ``select_package``. This screen will have to send this list to
        the endpoints it calls, so we can select/deselect lines but still
        show them in the list of the client application.

        Transitions:
        * select_line: nothing could be found for the barcode
        * select_package: lines are selected, user is redirected to this
        screen to change the qty done and destination package if needed
        """
        assert package_id or move_line_id

        picking = self.env["stock.picking"].browse(picking_id)
        if not picking.exists():
            return self._response_stock_picking_does_not_exist()

        message = self.actions_for("message")
        selection_lines = self._lines_to_pack(picking)
        # TODO if no remaining lines, go to summary

        if package_id:
            package = self.env["stock.quant.package"].browse(package_id).exists()
            if not package:
                return self._response_for_selected_stock_picking(
                    picking, message=message.record_not_found()
                )
            return self._select_lines_from_package(picking, selection_lines, package)
        if move_line_id:
            move_line = self.env["stock.move.line"].browse(move_line_id).exists()
            if not move_line:
                return self._response_for_selected_stock_picking(
                    picking, message=message.record_not_found()
                )
            # normally, the client should sent only move lines out of packages, but
            # in case there is a package, handle it as a package
            if move_line.package_id:
                return self._select_lines_from_package(
                    picking, selection_lines, move_line.package_id
                )
            self._select_lines(move_line)
            return self._response_for_select_package(move_line)

        return self._response()

    def _change_line_qty(
        self, picking_id, selected_line_ids, move_line_id, quantity_func
    ):
        picking = self.env["stock.picking"].browse(picking_id)
        if not picking.exists():
            return self._response_stock_picking_does_not_exist()

        message_directory = self.actions_for("message")

        move_line = self.env["stock.move.line"].browse(move_line_id).exists()

        message = None
        if not move_line:
            message = message_directory.record_not_found()
        else:
            qty_done = quantity_func(move_line)
            if qty_done > move_line.product_uom_qty:
                qty_done = move_line.product_uom_qty
                message = {
                    "message": _(
                        "Not allowed to pack more than the quantity, "
                        "the value has been changed to the maximum."
                    ),
                    "message_type": "warning",
                }
            if qty_done < 0:
                message = {
                    "message": _("Negative quantity not allowed."),
                    "message_type": "error",
                }
            else:
                move_line.qty_done = qty_done
        return self._response_for_select_package(
            self.env["stock.move.line"].browse(selected_line_ids).exists(),
            message=message,
        )

    def reset_line_qty(self, picking_id, selected_line_ids, move_line_id):
        """Reset qty_done of a move line to zero

        Used to deselect a line in the "select_package" screen.
        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as deselected
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, move_line_id, lambda __: 0
        )

    def set_line_qty(self, picking_id, selected_line_ids, move_line_id):
        """Set qty_done of a move line to its reserved quantity

        Used to select a line in the "select_package" screen.
        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as selected
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, move_line_id, lambda l: l.product_uom_qty
        )

    def set_custom_qty(self, picking_id, selected_line_ids, move_line_id, qty_done):
        """Change qty_done of a move line with a custom value

        The selected_line_ids parameter is used to keep the selection of lines
        stateless.

        Transitions:
        * select_package: goes back to this screen showing all the lines after
          we changed the qty
        """
        return self._change_line_qty(
            picking_id, selected_line_ids, move_line_id, lambda __: qty_done
        )

    def scan_package_action(self, picking_id, move_line_ids, barcode):
        """Scan a package, a lot, a product or a package to handle a line

        When a package is scanned, if the package is known as the destination
        package of one of the lines or is the source package of a selected
        line, the package is set to be the destination package of all then
        selected lines.

        When a product is scanned, it selects (set qty_done = reserved qty) or
        deselects (set qty_done = 0) the move lines for this product. Only
        products not tracked by lot can use this.

        When a lot is scanned, it does the same as for the products but based
        on the lot.

        When a packaging type (one without related product) is scanned, a new
        package is created and set as destination of the selected lines.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package.

        Transitions:
        * select_package: when a product or lot is scanned to select/deselect,
        the client app has to show the same screen with the updated selection
        * select_line: when a package or packaging type is scanned, move lines
        have been put in package and we can return back to this state to handle
        the other lines
        * summary: if there is no other lines, go to the summary screen to be able
        to close the stock picking
        """
        return self._response()

    def new_package(self, picking_id, move_line_ids):
        """Add all selected lines in a new package

        It creates a new package and set it as the destination package of all
        the selected lines.

        Selected lines are move lines in the list of ``move_line_ids`` where
        ``qty_done`` > 0 and have no destination package.

        Transitions:
        * select_line: goes back to selection of lines to work on next lines
        """
        return self._response()

    def list_dest_package(self, picking_id, move_line_ids):
        """Return a list of packages the user can select for the lines

        Only valid packages must be proposed. Look at ``scan_dest_package``
        for the conditions to be valid.

        Transitions:
        * select_dest_package: selection screen
        """
        return self._response()

    def scan_dest_package(self, picking_id, move_line_ids, barcode):
        """Scan destination package for lines

        Set the destination package on the selected lines with a `qty_done` if
        the package is valid. It is valid when one of:

        * it is already the destination package of another line of the stock.picking
        * it is the source package of the selected lines

        Note: by default, Odoo puts the same destination package as the source
        package on lines.

        Transitions:
        * select_package: error when scanning package
        * select_line: lines to package remain
        * summary: all lines are put in packages
        """
        return self._response()

    def set_dest_package(self, picking_id, move_line_ids, package_id):
        """Set destination package for lines from a package id

        Used by the list obtained from ``list_dest_package``.

        The validity is the same as ``scan_dest_package``.

        Transitions:
        * select_dest_package: error when scanning package
        * select_line: lines to package remain
        * summary: all lines are put in packages
        """
        return self._response()

    def summary(self, picking_id):
        """Return information for the summary screen

        Transitions:
        * summary
        """
        return self._response()

    def list_package_type(self, picking_id, package_id):
        """List the available package types for a package

        For a package, we can change the package type. The available
        package types are the ones with no product.

        Transitions:
        * change_package_type
        """
        return self._response()

    def set_package_type(self, picking_id, package_id, package_type_id):
        """Set a package type on a package

        Transitions:
        * change_package_type: in case of error
        * summary
        """
        return self._response()

    def remove_package(self, picking_id, package_id):
        """Remove destination package from move lines and set qty done to 0

        All the move lines with the package as ``result_package_id`` have their
        ``result_package_id`` reset to the source package (default odoo behavior)
        and their ``qty_done`` set to 0.

        Transitions:
        * summary
        """
        return self._response()

    def done(self, picking_id, confirmation=False):
        """Set the moves as done

        If some lines have not the full ``qty_done`` or no destination package set,
        a confirmation is asked to the user.

        Transitions:
        * summary: in case of error
        * select_document: after done, goes back to start
        * confirm_done: confirm a partial
        """
        return self._response()


class ShopfloorCheckoutValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.checkout.validator"
    _usage = "checkout.validator"

    def scan_document(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_stock_picking(self):
        return {}

    def select(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def select_line(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": False, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def reset_line_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_line_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_custom_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty_done": {"coerce": to_float, "required": True, "type": "float"},
        }

    def scan_package_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def new_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def list_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def scan_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def set_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def summary(self):
        return {"picking_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def list_package_type(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_package_type(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_type_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def remove_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def done(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorCheckoutValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.checkout.validator.response"
    _usage = "checkout.validator.response"

    _start_state = "select_document"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "select_document": {},
            "manual_selection": self._schema_selection_list,
            "select_line": self._schema_stock_picking_details,
            "select_package": self._schema_selected_lines,
            "change_quantity": self._schema_selected_lines,
            "select_dest_package": self._schema_select_package,
            "summary": self._schema_stock_picking_details,
            "change_package_type": self._schema_select_package_type,
            "confirm_done": self._schema_stock_picking_details,
        }

    @property
    def _schema_stock_picking_details(self):
        schema = self.schemas().picking()
        schema.update(
            {
                "move_lines": {
                    "type": "list",
                    "schema": {"type": "dict", "schema": self.schemas().move_line()},
                }
            }
        )
        return {"picking": {"type": "dict", "schema": schema}}

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().picking()},
            }
        }

    @property
    def _schema_select_package(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().move_line()},
            },
            "packages": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().package()},
            },
            "picking": {"type": "dict", "schema": self.schemas().picking()},
        }

    @property
    def _schema_select_package_type(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().move_line()},
            },
            "package_types": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().package_type()},
            },
            "picking": {"type": "dict", "schema": self.schemas().picking()},
        }

    @property
    def _schema_selected_lines(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas().picking()},
        }

    def scan_document(self):
        return self._response_schema(
            next_states={"select_document", "select_line", "summary"}
        )

    def list_stock_picking(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(
            next_states={"manual_selection", "summary", "select_line"}
        )

    def scan_line(self):
        return self._response_schema(next_states={"select_line", "select_package"})

    def select_line(self):
        return self.scan_line()

    def reset_line_qty(self):
        return self._response_schema(next_states={"select_package"})

    def set_line_qty(self):
        return self._response_schema(next_states={"select_package"})

    def set_custom_qty(self):
        return self._response_schema(next_states={"select_package"})

    def scan_package_action(self):
        return self._response_schema(
            next_states={"select_package", "select_line", "summary"}
        )

    def new_package(self):
        return self._response_schema(next_states={"select_line"})

    def list_dest_package(self):
        return self._response_schema(next_states={"select_dest_package"})

    def scan_dest_package(self):
        return self._response_schema(
            next_states={"select_package", "select_line", "summary"}
        )

    def set_dest_package(self):
        return self._response_schema(
            next_states={"select_dest_package", "select_line", "summary"}
        )

    def summary(self):
        return self._response_schema(next_states={"summary"})

    def list_package_type(self):
        return self._response_schema(next_states={"change_package_type"})

    def set_package_type(self):
        return self._response_schema(next_states={"change_package_type", "summary"})

    def remove_package(self):
        return self._response_schema(next_states={"summary"})

    def done(self):
        return self._response_schema(next_states={"summary", "confirm_done"})
