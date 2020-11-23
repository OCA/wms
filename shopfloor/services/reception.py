# Copyright 2020 Akretion (https://akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    BarcodeNotFoundError,
    CannotMovePickingType,
    DestLocationNotAllowed,
    OperationNotFoundError,
    ProductNotInOrder,
    StockPickingNotAvailable,
    StockPickingNotFound,
    TooMuchProductInCommandError,
    response_decorator,
)


class Reception(Component):
    """
    Methods for the Reception Process

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
    _name = "shopfloor.reception"
    _usage = "reception"
    _description = __doc__

    @staticmethod
    def _filter_lines_to_receive(move_line):
        return (
            move_line.product_uom_qty != move_line.qty_done
            and not move_line.shopfloor_checkout_done
        )

    def _create_data_for_scan_products(self, partner_id, move_line_ids):
        pickings = self.env["stock.picking"].search(
            self._search_picking_by_partner_id(partner_id),
            order=self._order_for_list_stock_picking(),
        )
        move_lines = pickings.mapped("move_line_ids")
        move_lines_picked = self.env["stock.move.line"].search(
            self._search_move_line_picked(partner_id),
            order=self._order_for_move_line(),
        )
        move_lines_picking = self.env["stock.move.line"].search(
            [("id", "in", move_line_ids)], order=self._order_for_move_line(),
        )
        move_lines_data = {
            "move_lines": self.data.move_lines(move_lines),
            "id": partner_id,
            "move_lines_picked": self.data.move_lines(move_lines_picked),
            "move_lines_picking": self.data.move_lines(move_lines_picking),
        }

        return move_lines_data

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    def _data_for_stock_picking(self, picking, done=False):
        data = self.data.picking(picking)
        line_picker = self._lines_checkout_done if done else self._lines_to_receive
        data.update(
            {
                "move_lines": self._data_for_move_lines(
                    line_picker(picking), with_packaging=done
                )
            }
        )
        return data

    def _deselect_lines(self, lines):
        lines.filtered(lambda l: not l.shopfloor_checkout_done).qty_done = 0

    def _domain_for_list_stock_picking(self):
        return [
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _get_move_line(self, move_line_filter, partner_id, move_lines_picking):
        product_move_lines = self.env["stock.move.line"].search(
            move_line_filter, order=self._order_for_move_line(),
        )

        if not product_move_lines.exists():
            move_lines_data = self._create_data_for_scan_products(
                partner_id, move_lines_picking,
            )
            raise ProductNotInOrder(
                state="scan_products", data=move_lines_data,
            )

        return product_move_lines

    def _search_picking_by_partner_id(self, partner_id, state="assigned"):
        return [
            ("state", "=", state),
            ("picking_type_id", "in", self.picking_types.ids),
            ("partner_id", "=", partner_id),
        ]

    def _search_move_line_picked(self, partner_id):
        return [
            ("picking_id.state", "=", "assigned"),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.partner_id", "=", partner_id),
            ("shopfloor_checkout_done", "=", True),
        ]

    def _search_move_line_by_product(self, partner_id, barcode):
        return [
            ("picking_id.state", "=", "assigned"),
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("picking_id.partner_id", "=", partner_id),
            ("product_id.barcode", "=", barcode),
            ("shopfloor_checkout_done", "!=", True),
            ("state", "not in", ("cancel", "done")),
        ]

    def _set_product_move_line_quantity(
        self, partner_id, product_move_lines, qty,
    ):
        quantity_to_add = qty
        move_line_index = 0

        while quantity_to_add > 0 and move_line_index < len(product_move_lines):
            current_move_line = product_move_lines[move_line_index]
            quantity_possible_to_add = (
                current_move_line.product_uom_qty - current_move_line.qty_done
            )
            quantity_added_to_move_line = min(quantity_possible_to_add, quantity_to_add)
            current_move_line.qty_done += quantity_added_to_move_line
            quantity_to_add -= quantity_added_to_move_line

            if current_move_line.qty_done == current_move_line.product_uom_qty:
                move_line_index += 1

        if quantity_to_add > 0:
            move_lines_data = self._create_data_for_scan_products(
                partner_id, product_move_lines.ids,
            )
            raise OperationNotFoundError(
                state="scan_products", data=move_lines_data,
            )

    def _lines_checkout_done(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_checkout_done)

    def _lines_to_receive(self, picking):
        return picking.move_line_ids.filtered(self._filter_lines_to_receive)

    def _order_for_list_stock_picking(self):
        return "scheduled_date asc, id asc"

    def _order_for_move_line(self):
        return "date asc, id asc"

    def _response_for_scan_products(self, partner_id, move_line_ids=None, message=None):
        move_lines_data = self._create_data_for_scan_products(
            partner_id, move_line_ids,
        )

        return self._response(
            next_state="scan_products", data=move_lines_data, message=message,
        )

    def _response_for_start(self, message=None):
        pickings = self.env["stock.picking"].search(
            self._domain_for_list_stock_picking(),
            order=self._order_for_list_stock_picking(),
        )
        partners = pickings.mapped("partner_id")
        partners_data = self.data.partners(partners)

        for partner in partners_data:
            pickings = self.env["stock.picking"].search(
                self._search_picking_by_partner_id(partner["id"]),
            )
            partner["picking_count"] = len(pickings)

        data = {"partners": partners_data}

        return self._response(next_state="start", data=data, message=message)

    def _response_for_select_document(self, message=None):
        return self._response(next_state="select_document", message=message)

    def _response_for_select_line(self, picking, message=None):
        if all(line.shopfloor_checkout_done for line in picking.move_line_ids):
            return self._response_for_summary(picking, message=message)
        return self._response(
            next_state="select_line",
            data={"picking": self._data_for_stock_picking(picking)},
            message=message,
        )

    def _response_for_summary(self, picking, need_confirm=False, message=None):
        return self._response(
            next_state="summary" if not need_confirm else "confirm_done",
            data={
                "picking": self._data_for_stock_picking(picking, done=True),
                "all_processed": not bool(self._lines_to_receive(picking)),
            },
            message=message,
        )

    def _select_lines(self, lines):
        for line in lines:
            if line.shopfloor_checkout_done:
                continue
            line.qty_done = line.product_uom_qty

        picking = lines.mapped("picking_id")
        other_lines = picking.move_line_ids - lines
        self._deselect_lines(other_lines)

    def _select_lines_from_package(self, picking, selection_lines, package):
        lines = selection_lines.filtered(lambda l: l.package_id == package)
        if not lines:
            return self._response_for_select_line(
                picking,
                message={
                    "message_type": "error",
                    "body": _("Package {} is not in the current transfer.").format(
                        package.name
                    ),
                },
            )
        self._select_lines(lines)
        return self._response_for_select_package(picking, lines)

    def _select_line_move_line(self, picking, selection_lines, move_line):
        if not move_line:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        # normally, the client should sent only move lines out of packages, but
        # in case there is a package, handle it as a package
        if move_line.package_id:
            return self._select_lines_from_package(
                picking, selection_lines, move_line.package_id
            )
        self._select_lines(move_line)
        return self._response_for_select_package(picking, move_line)

    def _select_line_package(self, picking, selection_lines, package):
        if not package:
            return self._response_for_select_line(
                picking, message=self.msg_store.record_not_found()
            )
        return self._select_lines_from_package(picking, selection_lines, package)

    def _select_picking(self, picking, state_for_error, data):
        if not picking:
            raise StockPickingNotFound(state_for_error, data)
        if picking.picking_type_id not in self.picking_types:
            raise CannotMovePickingType(state_for_error, data)
        if picking.state != "assigned":
            raise StockPickingNotAvailable(state_for_error, data)

        return self._response_for_select_line(picking)

    @response_decorator
    def list_vendor_with_pickings(self):
        return self._response_for_start()

    @response_decorator
    def list_move_lines(self, partner_id):
        """List stock.picking records available

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        return self._response_for_scan_products(partner_id)

    @response_decorator
    def scan_product(self, partner_id, barcode):
        product_move_lines = self._get_move_line(
            self._search_move_line_by_product(partner_id, barcode), partner_id, [],
        )

        self._set_product_move_line_quantity(
            partner_id, product_move_lines, 1,
        )

        return self._response_for_scan_products(partner_id, product_move_lines.ids)

    @response_decorator
    def set_quantity(self, partner_id, move_lines_picking, qty):
        product_move_lines = self._get_move_line(
            [("id", "in", move_lines_picking)], partner_id, [],
        )
        quantity_available = 0

        for line in product_move_lines:
            quantity_available += line.product_uom_qty

        if quantity_available < qty:
            move_lines_data = self._create_data_for_scan_products(
                partner_id, product_move_lines.ids,
            )
            raise TooMuchProductInCommandError(
                state="scan_products", data=move_lines_data,
            )

        for line in product_move_lines:
            line.qty_done = 0

        self._set_product_move_line_quantity(
            partner_id, product_move_lines, qty,
        )

        return self._response_for_scan_products(partner_id, product_move_lines.ids)

    @response_decorator
    def set_destination(self, partner_id, barcode, move_lines_picking, location_dest):
        product_move_lines = self._get_move_line(
            [("id", "in", move_lines_picking)], partner_id, [],
        )

        search = self._actions_for("search")

        location_dest = search.location_from_scan(barcode)

        if not location_dest:
            raise BarcodeNotFoundError(
                state="scan_products",
                data=self._create_data_for_scan_products(
                    partner_id, product_move_lines.ids,
                ),
            )

        # Here we assume that all move_line have the same destination
        if not location_dest.is_sublocation_of(
            product_move_lines[0].picking_id.location_dest_id
        ):
            raise DestLocationNotAllowed(
                state="scan_products",
                data=self._create_data_for_scan_products(
                    partner_id, product_move_lines.ids,
                ),
            )

        quantity_stored = 0

        for line in product_move_lines:
            quantity_stored += line.qty_done
            if line.qty_done == line.product_uom_qty:
                line.write({"location_dest_id": location_dest.id})
                line.shopfloor_checkout_done = True
            elif line.qty_done < line.product_uom_qty:
                new_line, qty_check = line._split_qty_to_be_done(line.qty_done)

                line.write({"location_dest_id": location_dest.id})
                line.shopfloor_checkout_done = True

        return self._response_for_scan_products(
            partner_id,
            [],
            {
                "message_type": "success",
                "body": _("{} {} put in {}").format(
                    quantity_stored,
                    product_move_lines[0].product_id.name,
                    location_dest.name,
                ),
            },
        )

    @response_decorator
    def reset_product(self, partner_id, move_lines_picking):
        product_move_lines = self._get_move_line(
            [("id", "in", move_lines_picking)], partner_id, [],
        )

        for line in product_move_lines:
            line.qty_done = 0

        return self._response_for_scan_products(
            partner_id,
            [],
            {"message_type": "success", "body": "Products put back in place"},
        )

    @response_decorator
    def finish_receipt(self, partner_id, move_lines_picked):
        # get move_lines
        # for all move_lines mark picking as done
        product_move_lines = self._get_move_line(
            [("id", "in", move_lines_picked)], partner_id, [],
        )

        for line in product_move_lines:
            line.shopfloor_checkout_done = False

        stock = self._actions_for("stock")
        stock.validate_moves(product_move_lines.mapped("move_id"))

        # for line in product_move_lines:
        #    picking = line.picking_id

        #    if picking.state == "done":
        #        continue

        #    picking.action_done()

        return self._response_for_start()


class ShopfloorReceptionValidator(Component):
    """Validators for the Checkout endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.reception.validator"
    _usage = "reception.validator"

    def list_vendor_with_pickings(self):
        return {}

    def list_move_lines(self):
        return {"partner_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_product(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_quantity(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_lines_picking": {
                "required": True,
                "type": "list",
                "schema": {"coerce": to_int, "type": "integer"},
            },
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_destination(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "move_lines_picking": {
                "required": True,
                "type": "list",
                "schema": {"coerce": to_int, "type": "integer"},
            },
            "location_dest": {"required": True, "type": "string"},
        }

    def finish_receipt(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_lines_picked": {
                "required": True,
                "type": "list",
                "schema": {"coerce": to_int, "type": "integer"},
            },
        }

    def reset_product(self):
        return {
            "partner_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_lines_picking": {
                "required": True,
                "type": "list",
                "schema": {"coerce": to_int, "type": "integer"},
            },
        }


class ShopfloorReceptionValidatorResponse(Component):
    """Validators for the Checkout endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.reception.validator.response"
    _usage = "reception.validator.response"

    _start_state = "start"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "manual_selection": self._schema_selection_list,
            "start": self._schema_partner_list,
            "summary": self._schema_summary,
            "scan_products": self._schema_for_move_lines_details,
        }

    def list_vendor_with_pickings(self):
        return self._response_schema(next_states={"start"})

    def list_move_lines(self):
        return self._response_schema(next_states={"scan_products"})

    def scan_product(self):
        return self._response_schema(next_states={"scan_products"})

    def set_quantity(self):
        return self._response_schema(next_states={"scan_products"})

    def set_destination(self):
        return self._response_schema(next_states={"scan_products"})

    def finish_receipt(self):
        return self._response_schema(next_states={"start"})

    def reset_product(self):
        return self._response_schema(next_states={"scan_products"})

    def _schema_stock_picking(self, lines_with_packaging=False):
        schema = self.schemas.picking()
        schema.update(
            {
                "move_lines": self.schemas._schema_list_of(
                    self.schemas.move_line(with_packaging=lines_with_packaging)
                )
            }
        )
        return {"picking": self.schemas._schema_dict_of(schema, required=True)}

    @property
    def _schema_stock_picking_details(self):
        return self._schema_stock_picking()

    @property
    def _schema_summary(self):
        return dict(
            self._schema_stock_picking(lines_with_packaging=True),
            all_processed={"type": "boolean"},
        )

    @property
    def _schema_partner_list(self):
        return {
            "partners": self.schemas._schema_list_of(
                self.schemas.partner(with_picking_count=True)
            ),
        }

    @property
    def _schema_selection_list(self):
        return {
            "pickings": self.schemas._schema_list_of(self.schemas.picking()),
        }

    @property
    def _schema_for_move_lines_details(self):
        return {
            "move_lines": self.schemas._schema_list_of(self.schemas.move_line()),
            "id": {"required": True, "type": "integer"},
            "move_lines_picked": self.schemas._schema_list_of(self.schemas.move_line()),
            "move_lines_picking": self.schemas._schema_list_of(
                self.schemas.move_line()
            ),
        }
