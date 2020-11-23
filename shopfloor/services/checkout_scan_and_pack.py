# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    BarcodeNotFoundError,
    NoMoreOrderToSkip,
    TooMuchProductInCommandError,
    response_decorator,
)


class CheckoutScanAndPack(Component):
    """
    Methods for the Checkout Process

    This scenario runs on existing moves.
    It happens on the "Packing" step of a pick/pack/ship.

    Use cases:

    1) Products are packed (e.g. full pallet shipping) and we keep the packages
    2) Products are packed (e.g. rollercage bins) and we create a new package
       with same content for shipping
    3) Products are packed (e.g. half-pallet ) and we merge several into one
    4) Products are packed (e.g. too high pallet) and we split it on several
    5) Products are not packed (e.g. raw products) and we create new packages
    6) Products are not packed (e.g. raw products) and we do not create packages

    A new flag ``shopfloor_checkout_done`` on move lines allows to track which
    lines have been checked out (can be with or without package).

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.checkout_scan_and_pack"
    _usage = "checkout_scan_and_pack"
    _description = __doc__

    def _get_data_for_scan_products(
        self, picking_id, move_line_id=None,
    ):
        picking = self.env["stock.picking"].browse(picking_id)
        move_line = self.env["stock.move.line"].browse(move_line_id)

        message = self._check_picking_status(picking)

        return (
            picking,
            move_line,
            message,
        )

    def _create_data_for_scan_products(
        self, picking,
    ):
        data = self.data.picking(picking)
        data.update(
            {
                "move_lines": self.data.move_lines(
                    picking.move_line_ids, with_package_dest=True
                )
            }
        )
        return data

    def _create_response_for_scan_products(
        self, picking, message=None, skip=None, confirm=False,
    ):
        return self._response(
            next_state="scan_products",
            data={
                "picking": self._create_data_for_scan_products(picking),
                "skip": skip,
                "confirm": confirm,
            },
            message=message,
        )

    def _set_move_line_qty(
        self, move_line, qty, picking,
    ):

        if qty > move_line.product_uom_qty:
            raise TooMuchProductInCommandError(
                state="scan_products",
                data=self._create_data_for_scan_products(picking),
            )

        move_line.qty_done = qty

        if move_line.qty_done == move_line.product_uom_qty:
            move_line.shopfloor_checkout_done = True
        else:
            move_line.shopfloor_checkout_done = False

    def _response_for_select_document(self, message=None):
        return self._response(next_state="start", message=message)

    def _select_picking(self, picking, state_for_error, skip=0):
        if not picking:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_found()
                )
            return self._response_for_select_document(
                message=self.msg_store.barcode_not_found()
            )
        if picking.picking_type_id not in self.picking_types:
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.cannot_move_something_in_picking_type()
                )
            return self._response_for_select_document(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )
        if picking.state != "assigned":
            if state_for_error == "manual_selection":
                return self._response_for_manual_selection(
                    message=self.msg_store.stock_picking_not_available(picking)
                )
            return self._response_for_select_document(
                message=self.msg_store.stock_picking_not_available(picking)
            )
        return self._create_response_for_scan_products(picking, skip=skip)

    def _data_for_stock_picking(self, picking, done=False):
        data = self.data.picking(picking)
        move_lines = picking.move_line_ids.filtered(
            lambda move_line: move_line.qty_done > 0
            and move_line.shopfloor_checkout_done
        )
        data.update(
            {
                "move_lines": self.data.move_lines(
                    move_lines, with_packaging=done, with_package_dest=True,
                )
            }
        )
        return data

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"

    @response_decorator
    def scan_document(self, barcode, skip=0):
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
        search = self._actions_for("search")
        picking = search.picking_from_scan(barcode)

        if not picking:
            location = search.location_from_scan(barcode)
            if location:
                if not location.is_sublocation_of(
                    self.picking_types.mapped("default_location_src_id")
                ):
                    return self._response_for_select_document(
                        message=self.msg_store.location_not_allowed()
                    )
                lines = location.source_move_line_ids.filtered(
                    lambda ml: ml.state not in ("cancel", "done")
                )

                pickings = lines.mapped("picking_id")
                if skip >= len(pickings):
                    picking = pickings[-1]
                    raise NoMoreOrderToSkip(
                        state="scan_products",
                        data={
                            "picking": self._create_data_for_scan_products(picking),
                            "skip": skip,
                        },
                    )
                picking = pickings[skip : skip + 1]  # take the first one

        if not picking:
            package = search.package_from_scan(barcode)
            if package:
                pickings = package.move_line_ids.filtered(
                    lambda ml: ml.state not in ("cancel", "done")
                ).mapped("picking_id")
                if len(pickings) > 1:
                    # Filter only if we find several pickings to narrow the
                    # selection to one of the good type. If we have one picking
                    # of the wrong type, it will be caught in _select_picking
                    # with the proper error message.
                    # Side note: rather unlikely to have several transfers ready
                    # and moving the same things
                    pickings = pickings.filtered(
                        lambda p: p.picking_type_id in self.picking_types
                    )
                if len(pickings) == 1:
                    picking = pickings
        return self._select_picking(picking, "select_document", skip)

    @response_decorator
    def scan_product(self, picking_id, barcode):
        """Adds 1 to a product quantity done

        if the qty_done of the move line reaches the product_uom_qty
        of the move line if sets shopfloor_checkout_done to True

        Transitions:
        * scan_products: in all cases
        """
        picking, _, message = self._get_data_for_scan_products(picking_id)

        if message:
            return self._response_for_select_document(message=message)

        # If there are more than one move_lines with the same product
        # just pick the first one that hasn't a quantity done equal to
        # it's target quantity
        move_lines = picking.move_line_ids.filtered(
            lambda l: l.product_id.barcode == barcode and not l.shopfloor_checkout_done
        )

        if len(move_lines) > 0:
            move_line = move_lines[0]
        else:
            raise BarcodeNotFoundError(
                state="scan_products",
                data={
                    "picking": self._create_data_for_scan_products(picking),
                    "skip": None,
                },
            )

        quantity_to_set = move_line.qty_done + 1

        self._set_move_line_qty(move_line, quantity_to_set, picking)

        return self._create_response_for_scan_products(picking, message)

    @response_decorator
    def set_quantity(self, picking_id, move_line_id, qty):
        """Sets qty to a product quantity done

        if the qty_done of the move line reaches the product_uom_qty
        of the move line if sets shopfloor_checkout_done to True

        if the quantity qty_done is set to a value less than product_uom_qty
        of the move it sets shopfloor_checkout_done to False

        Transitions:
        * scan_products: in all cases
        """
        picking, move_line, message = self._get_data_for_scan_products(
            picking_id, move_line_id,
        )

        if message:
            return self._response_for_select_document(message=message)

        self._set_move_line_qty(move_line, qty, picking)

        return self._create_response_for_scan_products(picking, message)

    @response_decorator
    def list_stock_picking(self):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * start: to the selection screen
        """
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )

        data = {"pickings": self.data.pickings(pickings)}

        return self._response(next_state="start", data=data)

    @response_decorator
    def done(self, picking_id, confirmation=False):
        """Set the moves as done

        If some lines have not the full ``qty_done`` or no destination package set,
        a confirmation is asked to the user.

        Transitions:
        * summary: in case of error
        * select_document: after done, goes back to start
        * confirm_done: confirm a partial
        """
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_status(picking)
        if message:
            return self._response_for_select_document(message=message)
        lines = picking.move_line_ids
        if not confirmation:
            if not all(line.qty_done == line.product_uom_qty for line in lines):
                return self._create_response_for_scan_products(picking, confirm=True,)
            elif not all(line.shopfloor_checkout_done for line in lines):
                return self._create_response_for_scan_products(
                    picking,
                    message={
                        "message_type": "warning",
                        "body": _("Remaining raw product not packed, proceed anyway"),
                    },
                    confirm=True,
                )
        # Here we should catch UserError for package cannot be moved more than once
        # And offer to create another package
        # odoo.exceptions.UserError:
        # ('You cannot move the same package content more than once in the same
        # transfer or split the same package into two location.', '')
        picking.action_done()
        return self._response_for_select_document(
            message=self.msg_store.transfer_done_success(picking)
        )


class ShopfloorCheckoutScanAndPackValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.checkout_scan_and_pack.validator"
    _usage = "checkout_scan_and_pack.validator"

    def scan_document(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "skip": {"coerce": to_int, "required": False, "type": "integer"},
        }

    def list_stock_picking(self):
        return {}

    def scan_product(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_quantity(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def done(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorCheckoutScanAndPackValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.checkout_scan_and_pack.validator.response"
    _usage = "checkout_scan_and_pack.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_selection_list,
            "scan_products": self._schema_stock_picking_details,
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
        return {
            "picking": self.schemas._schema_dict_of(schema, required=True),
            "skip": {"type": "integer", "nullable": True},
            "confirm": {"type": "boolean", "required": False, "nullable": True},
        }

    @property
    def _schema_stock_picking_details(self):
        return self._schema_stock_picking()

    @property
    def _schema_selection_list(self):
        return {
            "pickings": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.picking()},
            }
        }

    def scan_document(self):
        return self._response_schema(next_states={"scan_products"})

    def list_stock_picking(self):
        return self._response_schema(next_states={"start"})

    def scan_product(self):
        return self._response_schema(next_states={"scan_products"})

    def set_quantity(self):
        return self._response_schema(next_states={"scan_products"})

    def done(self):
        return self._response_schema(next_states={"scan_products", "start"})
