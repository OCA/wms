from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .service import to_float

# NOTE: we need to know if the destination package is set, but sometimes
# the dest. package is kept, so we should have an additional field on
# move lines to keep track of lines set


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
        if not picking:
            return self._response_for_no_stock_picking_found()
        if picking:
            if picking.picking_type_id != self.picking_type:
                return self._response_for_scan_picking_type_not_allowed()
            if picking.state != "assigned":
                return self._response_for_picking_not_assigned(picking)
            return self._response_for_selected_stock_picking(picking)

    def _response_for_selected_stock_picking(self, picking):
        # TODO if all lines have a dest package set, go to summary
        return self._response(
            next_state="select_line", data=self._data_for_stock_picking(picking)
        )

    def _response_for_picking_not_assigned(self, picking):
        return self._response(
            next_state="select_document",
            message={
                "message_type": "error",
                "message": _("Transfer {} is not entirely available.").format(
                    picking.name
                ),
            },
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

    def _response_for_no_stock_picking_found(self):
        message = self.actions_for("message")
        return self._response(
            next_state="select_document", message=message.barcode_not_found()
        )

    def _data_for_stock_picking(self, picking):
        return {
            "picking": {
                "id": picking.id,
                "name": picking.name,
                "origin": picking.origin or "",
                "note": picking.note or "",
                # TODO add partner
                "move_lines": [
                    {
                        "id": ml.id,
                        "qty_done": ml.qty_done,
                        "quantity": ml.product_uom_qty,
                        "product": {
                            "id": ml.product_id.id,
                            "name": ml.product_id.name,
                            "display_name": ml.product_id.display_name,
                            "default_code": ml.product_id.default_code or "",
                        },
                        "lot": {"id": ml.lot_id.id, "name": ml.lot_id.name}
                        if ml.lot_id
                        else None,
                        "package_src": {
                            "id": ml.package_id.id,
                            "name": ml.package_id.name,
                            # TODO
                            "weight": 0,
                            # TODO
                            "line_count": 0,
                            "package_type_name": (
                                ml.package_id.package_storage_type_id.name or ""
                            ),
                        }
                        if ml.package_id
                        else None,
                        "package_dest": {
                            "id": ml.result_package_id.id,
                            "name": ml.result_package_id.name,
                            # TODO
                            "weight": 0,
                            # TODO
                            "line_count": 0,
                            "package_type_name": (
                                ml.result_package_id.package_storage_type_id.name or ""
                            ),
                        }
                        if ml.result_package_id
                        else None,
                        "location_src": {
                            "id": ml.location_id.id,
                            "name": ml.location_id.name,
                        },
                        "location_dest": {
                            "id": ml.location_dest_id.id,
                            "name": ml.location_dest_id.name,
                        },
                    }
                    for ml in picking.move_line_ids
                ],
            }
        }

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "=", self.picking_type.id),
        ]

    def _order_for_list_stock_picking(self):
        return "scheduled_date desc, id asc"

    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        data = {
            "pickings": [self._data_picking_for_list(picking) for picking in pickings]
        }
        return self._response(next_state="manual_selection", data=data)

    def _data_picking_for_list(self, picking):
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
        return self._response()

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
        return self._response()

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
        return self._response()

    def reset_line_qty(self, picking_id, move_line_id):
        """Reset qty_done of a move line to zero

        Used to deselect a line in the "select_package" screen.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as deselected
        """
        return self._response()

    def set_line_qty(self, picking_id, move_line_id):
        """Set qty_done of a move line to its reserved quantity

        Used to deselect a line in the "select_package" screen.

        Transitions:
        * select_package: goes back to the same state, the line will appear
        as selected
        """
        return self._response()

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

    def set_custom_qty(self, picking_id, move_line_id, qty_done):
        """Change qty_done of a move line with a custom value

        Transitions:
        * select_package: goes back to this screen showing all the lines after
          we changed the qty
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
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_line_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def scan_package_action(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def set_custom_qty(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty_done": {"coerce": to_float, "required": True, "type": "float"},
        }

    def new_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def list_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
        }

    def scan_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {"coerce": to_int, "required": True, "type": "integer"},
            },
            "barcode": {"required": True, "type": "string"},
        }

    def set_dest_package(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_ids": {
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
        return {
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": True, "required": True},
                    "note": {"type": "string", "nullable": True, "required": True},
                    "move_lines": {
                        "type": "list",
                        "schema": {
                            "type": "dict",
                            "schema": self.schemas().move_line(),
                        },
                    },
                },
            }
        }

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                        "origin": {
                            "type": "string",
                            "nullable": True,
                            "required": True,
                        },
                        "note": {"type": "string", "nullable": True, "required": True},
                        "line_count": {"type": "integer", "required": True},
                        "partner": {
                            "type": "dict",
                            "nullable": True,
                            "required": True,
                            "schema": {
                                "id": {"required": True, "type": "integer"},
                                "name": {
                                    "type": "string",
                                    "nullable": False,
                                    "required": True,
                                },
                            },
                        },
                    },
                },
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
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": True, "required": True},
                    "note": {"type": "string", "nullable": True, "required": True},
                },
            },
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
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": True, "required": True},
                    "note": {"type": "string", "nullable": True, "required": True},
                },
            },
        }

    @property
    def _schema_selected_lines(self):
        return {
            "selected_move_lines": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas().move_line()},
            },
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": True, "required": True},
                    "note": {"type": "string", "nullable": True, "required": True},
                },
            },
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

    def scan_package_action(self):
        return self._response_schema(
            next_states={"select_package", "select_line", "summary"}
        )

    def set_custom_qty(self):
        return self._response_schema(next_states={"select_package"})

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
