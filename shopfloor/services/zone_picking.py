# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import functools
from itertools import groupby

from odoo.fields import first
from odoo.tools.float_utils import float_compare, float_is_zero

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float


class ZonePicking(Component):
    """
    Methods for the Zone Picking Process

    Zone picking of move lines.

    Note:

    * Several operation types could be linked to a single menu item
    * If several operator work in a same zone, they’ll see the same move lines but
      will only posts theirs when unloading their goods, which means that when they
      scan lines, the backend has to store the user id on the move lines

    Workflow:

    1. The operator scans the zone location with goods to pick (zone location
       meaning a parent location, not a leaf)
    2. If the zone contains lines from different picking types, the operator
       chooses the type to work with
    3. The client application shows the list of move lines, with an option
       to choose the sorting of the lines
    4. The operator selects a line to pick, by scanning one of:

       * location, if only a single move line there; if a location is scanned
         and it contains several move lines, the view is updated to show only
         them
       * package
       * product
       * lot

    5. The operator scans the destination for the line they scanned, this is where
       the path splits:

       * they scan a location, in which case the move line's destination is
         updated with it and the move is done
       * they scan a package, which becomes the destination package of the move
         line, the move line is not set to done, its ``qty_done`` is updated
         and a field ``shopfloor_user_id`` is set to the user; consider the
         move line is set in a buffer

    6. At any point, from the list of moves, the operator can reach the
       "unload" screens to unload what they had put into the buffer (scanned a
       destination package during step 5.). This is optional as they can directly
       move whole pallets by scanning the destination in step 5.
    7. The unload screens (similar to those of the Cluster Picking workflow) are
       used to move what has been put in the buffer:

       * if the original destination of all the lines is unique, screen allows
         to scan a single destination; they can use a "split" button to go to
         the line by line screen
       * if the lines have different destinations, they have to scan the destination
         package, then scan the destination location, scan the next package and its
         destination and so on.

    The list of move lines (point 4.) has support functions:

    * Change a lot or pack: if the expected lot is at the very bottom of the
      location or a stock error forces a user to change lot or pack, user can
      do it during the picking.
    * Declare stock out: if a good is in fact not in stock or only partially.
      Note the move lines may become unavailable or partially unavailable and
      generate a back-order.

    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.zone.picking"
    _usage = "zone_picking"
    _description = __doc__

    def _response_for_start(self, message=None):
        zones = self.work.menu.picking_type_ids.mapped(
            "default_location_src_id.child_ids"
        )
        return self._response(
            next_state="start",
            data={"zones": self._data_for_select_zone(zones)},
            message=message,
        )

    def _response_for_select_picking_type(
        self, zone_location, picking_types, message=None
    ):
        return self._response(
            next_state="select_picking_type",
            data=self._data_for_select_picking_type(zone_location, picking_types),
            message=message,
        )

    def _response_for_select_line(
        self, zone_location, picking_type, move_lines, message=None, popup=None
    ):
        return self._response(
            next_state="select_line",
            data=self._data_for_move_lines(zone_location, picking_type, move_lines),
            message=message,
            popup=popup,
        )

    def _response_for_set_line_destination(
        self,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_line(zone_location, picking_type, move_line)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="set_line_destination", data=data, message=message
        )

    def _response_for_zero_check(
        self, zone_location, picking_type, location, message=None
    ):
        return self._response(
            next_state="zero_check",
            data=self._data_for_location(zone_location, picking_type, location),
            message=message,
        )

    def _response_for_change_pack_lot(
        self, zone_location, picking_type, move_line, message=None
    ):
        return self._response(
            next_state="change_pack_lot",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
        )

    def _response_for_unload_all(
        self,
        zone_location,
        picking_type,
        move_lines,
        message=None,
        confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_lines(zone_location, picking_type, move_lines)
        data["confirmation_required"] = confirmation_required
        return self._response(next_state="unload_all", data=data, message=message)

    def _response_for_unload_single(
        self, zone_location, picking_type, move_line, message=None, popup=None
    ):
        buffer_lines = self._find_buffer_move_lines(zone_location, picking_type)
        completion_info = self.actions_for("completion.info")
        completion_info_popup = completion_info.popup(buffer_lines)
        return self._response(
            next_state="unload_single",
            data=self._data_for_move_line(zone_location, picking_type, move_line),
            message=message,
            popup=popup or completion_info_popup,
        )

    def _response_for_unload_set_destination(
        self,
        zone_location,
        picking_type,
        move_line,
        message=None,
        confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_line(zone_location, picking_type, move_line)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="unload_set_destination", data=data, message=message
        )

    def _data_for_select_picking_type(self, zone_location, picking_types):
        data = {
            "zone_location": self.data.location(zone_location),
            # available picking types to choose from
            "picking_types": self.data.picking_types(picking_types),
        }
        for datum in data["picking_types"]:
            picking_type = self.env["stock.picking.type"].browse(datum["id"])
            zone_lines = self._picking_type_zone_lines(zone_location, picking_type)
            datum.update(self._counters_for_zone_lines(zone_lines))
        return data

    def _counters_for_zone_lines(self, zone_lines):
        # Not using mapped/filtered to support simple lists and generators
        priority_lines = [x for x in zone_lines if x.picking_id.priority in ("2", "3")]
        return {
            "lines_count": len(zone_lines),
            "picking_count": len({x.picking_id.id for x in zone_lines}),
            "priority_lines_count": len(priority_lines),
            "priority_picking_count": len({x.picking_id.id for x in priority_lines}),
        }

    def _picking_type_zone_lines(self, zone_location, picking_type):
        domain = self._find_location_move_lines_domain(
            zone_location, picking_type=picking_type
        )
        return self.env["stock.move.line"].search(domain)

    def _data_for_move_line(self, zone_location, picking_type, move_line):
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "move_line": self.data.move_line(move_line, with_picking=True),
        }

    def _data_for_move_lines(self, zone_location, picking_type, move_lines):
        data = {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "move_lines": self.data.move_lines(move_lines, with_picking=True),
        }
        for data_move_line in data["move_lines"]:
            # TODO: this could be expensive, think about a better way
            # to retrieve if location will be empty.
            # Maybe group lines by location and compute only once.
            move_line = self.env["stock.move.line"].browse(data_move_line["id"])
            # `location_will_be_empty` flag states if, by processing this move line
            # and picking the product, the location will be emptied.
            data_move_line[
                "location_will_be_empty"
            ] = move_line.location_id.planned_qty_in_location_is_empty(move_line)
        return data

    def _data_for_location(self, zone_location, picking_type, location):
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "location": self.data.location(location),
        }

    def _zone_lines(self, zones):
        return self.env["stock.move.line"].search(
            self._find_location_move_lines_domain(zones)
        )

    def _data_for_select_zone(self, zones):
        """Retrieve detailed info for each zone.

        Zone without lines are skipped.
        Zone with lines will have line counters by operation type.

        :param zones: zone location recordset
        :return: see _schema_for_select_zone
        """
        res = []
        for zone in zones:
            zone_data = self.data.location(zone)
            zone_lines = self._zone_lines(zone).sorted(
                key=lambda x: x.picking_id.picking_type_id
            )
            if not zone_lines:
                continue
            zone_data["operation_types"] = []

            for picking_type, lines in groupby(
                zone_lines, lambda line: line.picking_id.picking_type_id
            ):
                op_type = self.data.picking_type(picking_type)
                op_type.update(self._counters_for_zone_lines(list(lines)))
                zone_data["operation_types"].append(op_type)
            res.append(zone_data)
        return res

    def _find_location_move_lines_domain(
        self, locations, picking_type=None, package=None, product=None, lot=None
    ):
        domain = [
            ("location_id", "child_of", locations.ids),
            ("qty_done", "=", 0),
            ("state", "in", ("assigned", "partially_available")),
        ]
        if picking_type:
            # auto_join in place for this field
            domain += [("picking_id.picking_type_id", "=", picking_type.id)]
        else:
            domain += [("picking_id.picking_type_id", "in", self.picking_types.ids)]
        if package:
            domain += [("package_id", "=", package.id)]
        if product:
            domain += [("product_id", "=", product.id)]
        if lot:
            domain += [("lot_id", "=", lot.id)]
        return domain

    def _find_location_move_lines(
        self,
        locations,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        order="priority",
    ):
        """Find lines that potentially need work in given locations."""
        move_lines = self.env["stock.move.line"].search(
            self._find_location_move_lines_domain(
                locations, picking_type, package, product, lot
            )
        )
        sort_keys_func, reverse = self._sort_key_move_lines(order)
        move_lines = move_lines.sorted(sort_keys_func, reverse=reverse)
        return move_lines

    @staticmethod
    def _sort_key_move_lines(order):
        """Return a `(sort_keys_func, reverse)` tuple for move lines."""
        if order == "priority":
            return lambda line: line.move_id.priority or "", True
        elif order == "location":
            return (
                lambda line: (
                    line.location_id.shopfloor_picking_sequence or "",
                    line.location_id.name,
                ),
                False,
            )

    def _find_buffer_move_lines_domain(
        self, zone_location, picking_type, dest_package=None
    ):
        domain = [
            ("location_id", "child_of", zone_location.id),
            ("qty_done", ">", 0),
            ("state", "not in", ("cancel", "done")),
            ("result_package_id", "!=", False),
            ("shopfloor_user_id", "=", self.env.user.id),
        ]
        if dest_package:
            domain.append(("result_package_id", "=", dest_package.id))
        return domain

    def _find_buffer_move_lines(self, zone_location, picking_type, dest_package=None):
        """Find lines that belongs to the operator's buffer and return them
        grouped by destination package.
        """
        domain = self._find_buffer_move_lines_domain(
            zone_location, picking_type, dest_package
        )
        return self.env["stock.move.line"].search(domain)

    def _group_buffer_move_lines_by_package(self, move_lines):
        data = {}
        for move_line in move_lines:
            data.setdefault(move_line.result_package_id, move_line.browse())
            data[move_line.result_package_id] |= move_line
        return data

    def select_zone(self):
        """Retrieve all available zones to work with.

        A zone is defined by the first level location below the source location
        of the operation types linked to the menu.

        The count of lines to process by available operations is computed per each zone.
        """
        return self._response_for_start()

    def scan_location(self, barcode):
        """Scan the zone location where the picking should occur

        The location must be a sub-location of one of the picking types'
        default source locations of the menu.

        Transitions:
        * start: invalid barcode
        * select_picking_type: the location is valid, user has to choose a picking type
        """
        search = self.actions_for("search")
        zone_location = search.location_from_scan(barcode)
        if not zone_location:
            return self._response_for_start(message=self.msg_store.no_location_found())
        if not zone_location.is_sublocation_of(
            self.work.menu.picking_type_ids.mapped("default_location_src_id")
        ):
            return self._response_for_start(
                message=self.msg_store.location_not_allowed()
            )
        move_lines = self._find_location_move_lines(zone_location)
        if not move_lines:
            return self._response_for_start(
                message=self.msg_store.no_lines_to_process()
            )
        picking_types = move_lines.picking_id.picking_type_id
        return self._response_for_select_picking_type(zone_location, picking_types)

    def list_move_lines(self, zone_location_id, picking_type_id, order="priority"):
        """List all move lines to pick, sorted

        Transitions:
        * select_line: show the list of move lines
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_location_move_lines(
            zone_location, picking_type, order=order
        )
        return self._response_for_select_line(zone_location, picking_type, move_lines)

    def _scan_source_location(
        self, zone_location, picking_type, location, order="priority"
    ):
        """Return the move line related to the scanned `location`.

        The method tries to identify unambiguously a move line in the location
        if possible, otherwise return `False`.
        """
        quants = self.env["stock.quant"].search([("location_id", "=", location.id)])
        product = quants.product_id
        lot = quants.lot_id
        package = quants.package_id
        if len(product) > 1 or len(lot) > 1 or len(package) > 1:
            return False
        domain = [("location_id", "=", location.id)]
        if product:
            domain.append(("product_id", "=", product.id))
            if lot:
                domain.append(("lot_id", "=", lot.id))
            if package:
                domain.append(("package_id", "=", package.id))
            move_lines = self.env["stock.move.line"].search(domain)
            sort_keys_func, reverse = self._sort_key_move_lines(order)
            move_lines = move_lines.sorted(sort_keys_func, reverse=reverse)
            return first(move_lines)
        return False

    def _scan_source_package(self, zone_location, picking_type, package, order):
        move_lines = self._find_location_move_lines(
            zone_location, picking_type, package=package, order=order
        )
        return first(move_lines)

    def _scan_source_product(self, zone_location, picking_type, product, order):
        move_lines = self._find_location_move_lines(
            zone_location, picking_type, product=product, order=order
        )
        return first(move_lines)

    def _scan_source_lot(self, zone_location, picking_type, lot, order):
        move_lines = self._find_location_move_lines(
            zone_location, picking_type, lot=lot, order=order
        )
        return first(move_lines)

    def scan_source(self, zone_location_id, picking_type_id, barcode, order="priority"):
        """Select a move line or narrow the list of move lines

        When the barcode is a location and we can unambiguously know which move
        line is picked (the quants in the location has one product/lot/package,
        matching a single move line), then the move line is selected.
        Otherwise, the list of move lines is refreshed with a filter on the
        scanned location, showing the move lines that have this location as
        source.

        When the barcode is a package, a product or a lot, the first matching
        line is selected.

        A selected line goes to the next screen to select the destination
        location or package.

        Transitions:
        * select_line: barcode not found or narrow the list on a location
        * set_line_destination: a line has been selected for picking
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        # select corresponding move line from barcode (location, package, product, lot)
        search = self.actions_for("search")
        move_line = self.env["stock.move.line"]
        location = search.location_from_scan(barcode)
        if location:
            if not location.is_sublocation_of(zone_location):
                return self._response_for_start(
                    message=self.msg_store.location_not_allowed()
                )
            move_line = self._scan_source_location(
                zone_location, picking_type, location, order=order
            )
            # if no move line, narrow the list of move lines on the scanned location
            if not move_line:
                response = self.list_move_lines(location.id, picking_type.id)
                return self._response(
                    base_response=response,
                    message=self.msg_store.several_lines_in_location(location),
                )
        package = search.package_from_scan(barcode)
        if package:
            move_line = self._scan_source_package(
                zone_location, picking_type, package, order
            )
            if not move_line:
                response = self.list_move_lines(zone_location.id, picking_type.id)
                return self._response(
                    base_response=response, message=self.msg_store.package_not_found()
                )
        product = search.product_from_scan(barcode)
        if product:
            move_line = self._scan_source_product(
                zone_location, picking_type, product, order
            )
            if not move_line:
                response = self.list_move_lines(zone_location.id, picking_type.id)
                return self._response(
                    base_response=response, message=self.msg_store.product_not_found()
                )
        lot = search.lot_from_scan(barcode)
        if lot:
            move_line = self._scan_source_lot(zone_location, picking_type, lot, order)
            if not move_line:
                response = self.list_move_lines(zone_location.id, picking_type.id)
                return self._response(
                    base_response=response, message=self.msg_store.lot_not_found()
                )
        # barcode not found, get back on 'select_line' screen
        if not move_line:
            response = self.list_move_lines(zone_location.id, picking_type.id)
            return self._response(
                base_response=response, message=self.msg_store.barcode_not_found()
            )
        return self._response_for_set_line_destination(
            zone_location, picking_type, move_line
        )

    def _set_destination_location(
        self, zone_location, picking_type, move_line, quantity, confirmation, location
    ):
        location_changed = False
        response = None

        # A valid location is a sub-location of the original destination, or a
        # any sub-location of the picking type's default destination location
        # if `confirmation is True
        # Ask confirmation to the user if the scanned location is not in the
        # expected ones but is valid (in picking type's default destination)
        if not location.is_sublocation_of(
            picking_type.default_location_dest_id
        ) or not location.is_sublocation_of(
            move_line.move_id.location_dest_id, func=all
        ):
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.dest_location_not_allowed(),
            )
            return (location_changed, response)

        if (
            not location.is_sublocation_of(move_line.location_dest_id)
            and not confirmation
        ):
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.confirm_location_changed(
                    move_line.location_dest_id, location
                ),
                confirmation_required=True,
            )
            return (location_changed, response)

        # If no destination package
        if not move_line.result_package_id:
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.dest_package_required(),
            )
            return (location_changed, response)
        # destination location set to the scanned one
        self._write_destination_on_lines(move_line, location)
        # the quantity done is set to the passed quantity
        move_line.qty_done = quantity
        # if the move has other move lines, it is split to have only this move line
        move_line.move_id.split_other_move_lines(move_line)
        # try to re-assign any split move (in case of partial qty)
        if "confirmed" in move_line.picking_id.move_lines.mapped("state"):
            move_line.picking_id.action_assign()
        move_line.move_id.extract_and_action_done()
        location_changed = True
        # Zero check
        zero_check = picking_type.shopfloor_zero_check
        if zero_check and move_line.location_id.planned_qty_in_location_is_empty():
            response = self._response_for_zero_check(
                zone_location, picking_type, move_line.location_id
            )
        return (location_changed, response)

    def _is_package_empty(self, package):
        return not bool(package.quant_ids)

    def _is_package_already_used(self, package):
        return bool(
            self.env["stock.move.line"].search_count(
                [
                    ("state", "not in", ("done", "cancel")),
                    ("result_package_id", "=", package.id),
                ]
            )
        )

    def _move_line_compare_qty(self, move_line, qty):
        rounding = move_line.product_uom_id.rounding
        return float_compare(
            qty, move_line.product_uom_qty, precision_rounding=rounding
        )

    def _move_line_full_qty(self, move_line, qty):
        rounding = move_line.product_uom_id.rounding
        return float_is_zero(
            move_line.product_uom_qty - qty, precision_rounding=rounding
        )

    def _set_destination_package(
        self, zone_location, picking_type, move_line, quantity, package
    ):
        package_changed = False
        response = None
        # A valid package is:
        # * an empty package
        # * not used as destination for another move line
        if not self._is_package_empty(package):
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.package_not_empty(package),
            )
            return (package_changed, response)
        if self._is_package_already_used(package):
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.package_already_used(package),
            )
            return (package_changed, response)
        # the quantity done is set to the passed quantity
        # but if we move a partial qty, we need to split the move line
        compare = self._move_line_compare_qty(move_line, quantity)
        qty_lesser = compare == -1
        qty_greater = compare == 1
        if qty_greater:
            response = self._response_for_set_line_destination(
                zone_location,
                picking_type,
                move_line,
                message=self.msg_store.unable_to_pick_more(move_line.product_uom_qty),
            )
            return (package_changed, response)
        elif qty_lesser:
            # split the move line which will be processed later
            remaining = move_line.product_uom_qty - quantity
            move_line.copy({"product_uom_qty": remaining, "qty_done": 0})
            # if we didn't bypass reservation update, the quant reservation
            # would be reduced as much as the deduced quantity, which is wrong
            # as we only moved the quantity to a new move line
            move_line.with_context(
                bypass_reservation_update=True
            ).product_uom_qty = quantity
        move_line.qty_done = quantity
        # destination package is set to the scanned one
        move_line.result_package_id = package
        # the field ``shopfloor_user_id`` is updated with the current user
        move_line.shopfloor_user_id = self.env.user
        package_changed = True
        # Zero check
        zero_check = picking_type.shopfloor_zero_check
        if zero_check and move_line.location_id.planned_qty_in_location_is_empty():
            response = self._response_for_zero_check(
                zone_location, picking_type, move_line.location_id
            )
        return (package_changed, response)

    def set_destination(
        self,
        zone_location_id,
        picking_type_id,
        move_line_id,
        barcode,
        quantity,
        confirmation=False,
        order="priority",
    ):
        """Set a destination location (and done) or a destination package (in buffer)

        When a line is picked, it can either:

        * be moved directly to a destination location, typically a pallet
        * be moved to a destination package, that we'll call buffer in the docstrings

        When the barcode is a valid location, actions on the move line:

        * destination location set to the scanned one
        * the quantity done is set to the passed quantity
        * if the move has other move lines, it is split to have only this move line
        * set to done (without backorder)

        A valid location is a sub-location of the original destination, or a
        sub-location of the picking type's default destination location if
        ``confirmation`` is True.

        When the barcode is a valid package, actions on the move line:

        * destination package is set to the scanned one
        * the quantity done is set to the passed quantity
        * the field ``shopfloor_user_id`` is updated with the current user

        Those fields will be used to identify which move lines are in the buffer.

        A valid package is:

        * an empty package
        * not used as destination for another move line

        Transitions:
        * select_line: destination has been set, showing the next lines to pick
        * zero_check: if the option is active and if the quantity of product
          moved is 0 in the source location after the move (beware: at this
          point the product we put in the buffer is still considered to be in
          the source location, so we have to compute the source location's
          quantity - qty_done).
        * set_line_destination: the scanned location is invalid, user has to
          scan another one
        * confirm_set_line_destination: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())

        pkg_moved = False
        search = self.actions_for("search")
        accept_only_package = not self._move_line_full_qty(move_line, quantity)

        if not accept_only_package:
            # When the barcode is a location
            location = search.location_from_scan(barcode)
            if location:
                pkg_moved, response = self._set_destination_location(
                    zone_location,
                    picking_type,
                    move_line,
                    quantity,
                    confirmation,
                    location,
                )
                if response:
                    return response

        # When the barcode is a package
        package = search.package_from_scan(barcode)
        if package:
            location = move_line.location_dest_id
            pkg_moved, response = self._set_destination_package(
                zone_location, picking_type, move_line, quantity, package
            )
            if response:
                return response

        message = None

        if not pkg_moved and not package:
            if accept_only_package:
                message = self.msg_store.package_not_found_for_barcode(barcode)
            else:
                # we don't know if user wanted to scan a location or a package
                message = self.msg_store.barcode_not_found()
            return self._response_for_set_line_destination(
                zone_location, picking_type, move_line, message=message
            )

        if pkg_moved:
            message = self.msg_store.confirm_pack_moved()

        # Process the next line
        response = self.list_move_lines(zone_location.id, picking_type.id)
        return self._response(base_response=response, message=message)

    def is_zero(self, zone_location_id, picking_type_id, move_line_id, zero):
        """Confirm or not if the source location of a move has zero qty

        If the user confirms there is zero quantity, it means the stock was
        correct and there is nothing to do. If the user says "no", a draft
        empty inventory is created for the product (with lot if tracked).

        Transitions:
        * select_line: whether the user confirms or not the location is empty,
          go back to the picking of lines
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        if not zero:
            inventory = self.actions_for("inventory")
            inventory.create_draft_check_empty(
                move_line.location_id,
                # FIXME as zero_check is done on the whole location, we should
                # create an inventory on it without the product critera
                # => the same applies on "Cluster Picking" scenario
                # move_line.product_id,
                move_line.product_id.browse(),  # HACK send an empty recordset
                ref=picking_type.name,
            )
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        return self._response_for_select_line(zone_location, picking_type, move_lines)

    def _domain_stock_issue_unlink_lines(self, move_line):
        # Since we have not enough stock, delete the move lines, which will
        # in turn unreserve the moves. The moves lines we delete are those
        # in the same location, and not yet started.
        # The goal is to prevent the same operator to declare twice the same
        # stock issue for the same product/lot/package.
        move = move_line.move_id
        lot = move_line.lot_id
        package = move_line.package_id
        location = move_line.location_id
        domain = [
            ("location_id", "=", location.id),
            ("product_id", "=", move.product_id.id),
            ("package_id", "=", package.id),
            ("lot_id", "=", lot.id),
            ("state", "not in", ("cancel", "done")),
            ("qty_done", "=", 0),
        ]
        return domain

    def stock_issue(self, zone_location_id, picking_type_id, move_line_id):
        """Declare a stock issue for a line

        After errors in the stock, the user cannot take all the products
        because there is physically not enough goods. The move line is deleted
        (unreserve), and an inventory is created to reduce the quantity in the
        source location to prevent future errors until a correction. Beware:
        the quantity already reserved and having a qty_done set on other lines
        in the same location should remain reserved so the inventory's quantity
        must be set to the total of qty_done of other lines.

        The other lines not yet picked (no qty_done) in the same location for
        the same product, lot, package are unreserved as well (moves lines
        deleted, which unreserve their quantity on the move).

        A second inventory is created in draft to have someone do an inventory
        check.

        At the end, it tries to reserve the goods again, and if the current
        line could be reserved in the current zone location, it transitions
        directly to the screen to set the destination.

        Transitions:
        * select_line: go back to the picking of lines for the next ones (nothing
          could be reserved as replacement)
        * set_line_destination: something could be reserved instead of the original
          move line
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        inventory = self.actions_for("inventory")
        # create a draft inventory for a user to check
        inventory.create_control_stock(
            move_line.location_id,
            move_line.product_id,
            move_line.package_id,
            move_line.lot_id,
        )
        move = move_line.move_id
        lot = move_line.lot_id
        package = move_line.package_id
        location = move_line.location_id

        # unreserve every lines for the same product/lot in the same location and
        # not done yet, so the same user doesn't have to declare 2 times the
        # stock issue for the same thing!
        domain = self._domain_stock_issue_unlink_lines(move_line)
        unreserve_move_lines = move_line | self.env["stock.move.line"].search(domain)
        unreserve_moves = unreserve_move_lines.mapped("move_id").sorted()
        unreserve_move_lines.unlink()

        # Then, create an inventory with just enough qty so the other assigned
        # move lines for the same product in other batches and the other move lines
        # already picked stay assigned.
        inventory.create_stock_issue(move, location, package, lot)

        # try to reassign the moves in case we have stock in another location
        unreserve_moves._action_assign()

        if move.move_line_ids:
            return self._response_for_set_line_destination(
                zone_location, picking_type, move.move_line_ids[0]
            )
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        return self._response_for_select_line(zone_location, picking_type, move_lines)

    def change_pack_lot(self, zone_location_id, picking_type_id, move_line_id, barcode):
        """Change the source package or the lot of a move line

        If the expected lot or package is at the very bottom of the location or
        a stock error forces a user to change lot or package, user can change the
        package or lot of the current move line.

        If the pack or lot was not supposed to be in the source location,
        a draft inventory is created to have this checked.

        Transitions:
        * change_pack_lot: the barcode scanned is invalid or change could not be done
        * set_line_destination: the package / lot has been changed, can be
          moved to destination now
        * select_line: if the move line does not exist anymore
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        search = self.actions_for("search")
        # pre-configured callable used to generate the response as the
        # change.package.lot component is not aware of the needed response type
        # and related parameters for zone picking scenario
        response_ok_func = functools.partial(
            self._response_for_set_line_destination, zone_location, picking_type
        )
        response_error_func = functools.partial(
            self._response_for_change_pack_lot, zone_location, picking_type
        )
        response = None
        change_package_lot = self.actions_for("change.package.lot")
        # handle lot
        lot = search.lot_from_scan(barcode)
        if lot:
            response = change_package_lot.change_lot(
                move_line, lot, response_ok_func, response_error_func
            )
        # handle package
        package = search.package_from_scan(barcode)
        if package:
            return change_package_lot.change_package(
                move_line, package, response_ok_func, response_error_func
            )
        # if the response is not an error, we check the move_line status
        # to adapt the response ('set_line_destination' or 'select_line')
        # TODO not sure to understand how 'move_line' could not exist here?
        if response and response["message"]["message_type"] == "success":
            # TODO adapt the response based on the move_line.exists()
            if move_line.exists():
                return response
            return response

        return self._response_for_change_pack_lot(
            zone_location,
            picking_type,
            move_line,
            message=self.msg_store.no_package_or_lot_for_barcode(barcode),
        )

    def prepare_unload(self, zone_location_id, picking_type_id):
        """Initiate the unloading of the buffer

        The buffer is composed of move lines:

        * in the current zone location and picking type
        * not done or canceled
        * with a qty_done > 0
        * have a destination package
        * with ``shopfloor_user_id`` equal to the current user

        The lines are grouped by their destination package. The destination
        package is what is shown on the screen (with their content, which is
        the move lines with the package as destination), and this is what is
        passed along in the ``package_id`` parameters in the unload methods.

        It goes to different screens depending if there is only one move line,
        or if all the move lines have the same destination or not.

        Transitions:
        * unload_single: move lines have different destinations, return data
          for the next destination package
        * unload_set_destination: there is only one move line in the buffer
        * unload_all: the move lines in the buffer all have the same
          destination location
        * select_line: no remaining move lines in buffer
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_buffer_move_lines(zone_location, picking_type)
        location_dest = move_lines.mapped("location_dest_id")
        if len(move_lines) == 1:
            return self._response_for_unload_set_destination(
                zone_location, picking_type, move_lines
            )
        elif len(move_lines) > 1 and len(location_dest) == 1:
            return self._response_for_unload_all(
                zone_location, picking_type, move_lines
            )
        elif len(move_lines) > 1 and len(location_dest) > 1:
            return self._response_for_unload_single(
                zone_location, picking_type, first(move_lines)
            )
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        return self._response_for_select_line(zone_location, picking_type, move_lines)

    def _set_destination_all_response(
        self, zone_location, picking_type, buffer_lines, message=None
    ):
        if buffer_lines:
            return self._response_for_unload_all(
                zone_location, picking_type, buffer_lines, message=message
            )
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        if move_lines:
            return self._response_for_select_line(
                zone_location, picking_type, move_lines, message=message
            )
        return self._response_for_start(message=message)

    def set_destination_all(
        self, zone_location_id, picking_type_id, barcode, confirmation=False
    ):
        """Set the destination for all the lines in the buffer

        Look in ``prepare_unload`` for the definition of the buffer.

        This method must be used only if all the buffer's move lines which have
        a destination package, qty done > 0, and have the same destination
        location.

        A scanned location outside of the destination location of the operation
        type is invalid.

        The move lines are then set to done, without backorders.

        Transitions:
        * unload_all: the scanned destination is invalid, user has to
          scan another one
        * unload_all + confirmation: the scanned location is not in the
          expected one but is valid (in picking type's default destination)
        * select_line: no remaining move lines in buffer
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        search = self.actions_for("search")
        location = search.location_from_scan(barcode)
        message = None
        buffer_lines = self._find_buffer_move_lines(zone_location, picking_type)
        if location:
            error = None
            location_dest = buffer_lines.mapped("location_dest_id")
            # check if move lines share the same destination
            if len(location_dest) != 1:
                error = self.msg_store.lines_different_dest_location()
            # check if the scanned location is allowed
            if not location.is_sublocation_of(picking_type.default_location_dest_id):
                error = self.msg_store.location_not_allowed()
            if error:
                return self._set_destination_all_response(
                    zone_location, picking_type, buffer_lines, message=error
                )
            # check if the destination location is not the expected one
            #   - OK if the scanned destination is a child of the current
            #     destination set on buffer lines
            #   - To confirm if the scanned destination is not a child of the
            #     current destination set on buffer lines
            if not location.is_sublocation_of(buffer_lines.location_dest_id):
                if not confirmation:
                    return self._response_for_unload_all(
                        zone_location,
                        picking_type,
                        buffer_lines,
                        message=self.msg_store.confirm_location_changed(
                            first(buffer_lines.location_dest_id), location
                        ),
                        confirmation_required=True,
                    )
            # the scanned location is still valid, use it
            self._write_destination_on_lines(buffer_lines, location)
            # set lines to done + refresh buffer lines (should be empty)
            moves = buffer_lines.mapped("move_id")
            moves.extract_and_action_done()
            message = self.msg_store.buffer_complete()
            buffer_lines = self._find_buffer_move_lines(zone_location, picking_type)
        else:
            message = self.msg_store.no_location_found()
        return self._set_destination_all_response(
            zone_location, picking_type, buffer_lines, message=message
        )

    def _write_destination_on_lines(self, lines, location):
        self._lock_lines(lines)
        lines.location_dest_id = location
        lines.package_level_id.location_dest_id = location

    def unload_split(self, zone_location_id, picking_type_id):
        """Indicates that now the buffer must be treated line per line

        Called from a button, users decides to handle destinations one by one.
        Even if the move lines to unload all have the same destination.

        Look in ``prepare_unload`` for the definition of the buffer.

        Transitions:
        * unload_single: more than one remaining line in the buffer
        * unload_set_destination: there is only one remaining line in the buffer
        * select_line: no remaining move lines in buffer
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        buffer_lines = self._find_buffer_move_lines(zone_location, picking_type)
        # more than one remaining move line in the buffer
        if len(buffer_lines) > 1:
            return self._response_for_unload_single(
                zone_location, picking_type, first(buffer_lines)
            )
        # only one move line to process in the buffer
        elif len(buffer_lines) == 1:
            return self._response_for_unload_set_destination(
                zone_location, picking_type, first(buffer_lines)
            )
        # no remaining move lines in buffer
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        return self._response_for_select_line(
            zone_location,
            picking_type,
            move_lines,
            message=self.msg_store.buffer_complete(),
        )

    def _unload_response(self, zone_location, picking_type, unload_single_message=None):
        """Prepare the right response depending on the move lines to process."""
        # if there are still move lines to process from the buffer
        move_lines = self._find_buffer_move_lines(zone_location, picking_type)
        if move_lines:
            return self._response_for_unload_single(
                zone_location,
                picking_type,
                first(move_lines),
                message=unload_single_message,
            )
        # if there are still move lines to process from the picking type
        #   => buffer complete!
        move_lines = self._find_location_move_lines(zone_location, picking_type)
        if move_lines:
            return self._response_for_select_line(
                zone_location,
                picking_type,
                move_lines,
                message=self.msg_store.buffer_complete(),
            )
        # no more move lines to process from the current picking type
        #   => picking type complete!
        return self._response_for_start(
            message=self.msg_store.picking_type_complete(picking_type)
        )

    def unload_scan_pack(self, zone_location_id, picking_type_id, package_id, barcode):
        """Scan the destination package to check user moves the good one

        The "unload_single" screen proposes a package (which has been
        previously been set as destination package of lines of the buffer).
        The user has to scan the package to validate they took the good one.

        Transitions:
        * unload_single: the scanned barcode does not match the package
        * unload_set_destination: the scanned barcode matches the package
        * select_line: no remaining move lines in buffer
        * start: no remaining move lines in picking type
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package = self.env["stock.quant.package"].browse(package_id)
        if not package.exists():
            return self._unload_response(
                zone_location,
                picking_type,
                unload_single_message=self.msg_store.record_not_found(),
            )
        search = self.actions_for("search")
        scanned_package = search.package_from_scan(barcode)
        # the scanned barcode matches the package
        if scanned_package == package:
            move_lines = self._find_buffer_move_lines(
                zone_location, picking_type, dest_package=scanned_package
            )
            if move_lines:
                return self._response_for_unload_set_destination(
                    zone_location, picking_type, first(move_lines)
                )
        return self._unload_response(
            zone_location,
            picking_type,
            unload_single_message=self.msg_store.barcode_no_match(package.name),
        )

    def _lock_lines(self, lines):
        """Lock move lines"""
        sql = "SELECT id FROM %s WHERE ID IN %%s FOR UPDATE" % lines._table
        self.env.cr.execute(sql, (tuple(lines.ids),), log_exceptions=False)

    def unload_set_destination(
        self, zone_location_id, picking_type_id, package_id, barcode, confirmation=False
    ):
        """Scan the final destination for move lines in the buffer with the
        destination package

        All the move lines in the buffer with the package_id as destination
        package are updated with the scanned location.

        The move lines are then set to done, without backorders.

        Look in ``prepare_unload`` for the definition of the buffer.

        Transitions:
        * unload_single: buffer still contains move lines, unload the next package
        * unload_set_destination: the scanned location is invalid, user has to
          scan another one
        * unload_set_destination+confirmation_required: the scanned location is not
          in the expected one but is valid (in picking type's default destination)
        * select_line: no remaining move lines in buffer
        * start: no remaining move lines to process in the picking type
        """
        zone_location = self.env["stock.location"].browse(zone_location_id)
        if not zone_location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        picking_type = self.env["stock.picking.type"].browse(picking_type_id)
        if not picking_type.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package = self.env["stock.quant.package"].browse(package_id)
        buffer_lines = self._find_buffer_move_lines(
            zone_location, picking_type, dest_package=package
        )
        if not package.exists() or not buffer_lines:
            move_lines = self._find_location_move_lines(zone_location, picking_type)
            return self._response_for_select_line(
                zone_location,
                picking_type,
                move_lines,
                message=self.msg_store.record_not_found(),
            )
        search = self.actions_for("search")
        location = search.location_from_scan(barcode)
        if location:
            if not location.is_sublocation_of(
                picking_type.default_location_dest_id
            ) or not location.is_sublocation_of(
                buffer_lines.move_id.location_dest_id, func=all
            ):
                return self._response_for_unload_set_destination(
                    zone_location,
                    picking_type,
                    first(buffer_lines),
                    message=self.msg_store.dest_location_not_allowed(),
                )
            # check if the destination location is not the expected one
            #   - OK if the scanned destination is a child of the current
            #     destination set on buffer lines
            #   - To confirm if the scanned destination is not a child of the
            #     current destination set on buffer lines
            if not location.is_sublocation_of(buffer_lines.location_dest_id):
                if not confirmation:
                    return self._response_for_unload_set_destination(
                        zone_location,
                        picking_type,
                        first(buffer_lines),
                        message=self.msg_store.confirm_location_changed(
                            first(buffer_lines.location_dest_id), location
                        ),
                        confirmation_required=True,
                    )
            # the scanned location is valid, use it
            self._write_destination_on_lines(buffer_lines, location)
            # set lines to done + refresh buffer lines (should be empty)
            moves = buffer_lines.mapped("move_id")
            # split move lines to a backorder move
            # if quantity is not fully satisfied
            for move in moves:
                move.split_other_move_lines(buffer_lines & move.move_line_ids)

            moves.extract_and_action_done()
            buffer_lines = self._find_buffer_move_lines(zone_location, picking_type)

            if buffer_lines:
                # TODO: return success message if line has been processed
                return self._response_for_unload_single(
                    zone_location, picking_type, first(buffer_lines)
                )
            move_lines = self._find_location_move_lines(zone_location, picking_type)
            if move_lines:
                return self._response_for_select_line(
                    zone_location,
                    picking_type,
                    move_lines,
                    message=self.msg_store.buffer_complete(),
                )
            return self._response_for_start(
                message=self.msg_store.picking_type_complete(picking_type)
            )
        # TODO: when we have no lines here
        # we should not redirect to `unload_set_destination`
        # because we'll have nothing to display (currently the UI is broken).
        return self._response_for_unload_set_destination(
            zone_location,
            picking_type,
            first(buffer_lines),
            message=self.msg_store.no_location_found(),
        )


class ShopfloorZonePickingValidator(Component):
    """Validators for the Zone Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.zone_picking.validator"
    _usage = "zone_picking.validator"

    def select_zone(self):
        return {}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def list_move_lines(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
        }

    def scan_source(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
        }

    def set_destination(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "order": {
                "required": False,
                "type": "string",
                "allowed": ["priority", "location"],
            },
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def is_zero(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "zero": {"coerce": to_bool, "required": True, "type": "boolean"},
        }

    def stock_issue(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def change_pack_lot(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def prepare_unload(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_destination_all(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def unload_split(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def unload_scan_pack(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def unload_set_destination(self):
        return {
            "zone_location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "picking_type_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorZonePickingValidatorResponse(Component):
    """Validators for the Zone Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.zone_picking.validator.response"
    _usage = "zone_picking.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": self._schema_for_select_zone,
            "select_picking_type": self._schema_for_select_picking_type,
            "select_line": self._schema_for_move_lines_empty_location,
            "set_line_destination": self._schema_for_move_line,
            "zero_check": self._schema_for_zero_check,
            "change_pack_lot": self._schema_for_move_line,
            "unload_all": self._schema_for_move_lines,
            "unload_single": self._schema_for_move_line,
            "unload_set_destination": self._schema_for_move_line,
        }

    def select_zone(self):
        return self._response_schema(next_states={"start"})

    def scan_location(self):
        return self._response_schema(next_states={"start", "select_picking_type"})

    def list_move_lines(self):
        return self._response_schema(next_states={"select_line"})

    def scan_source(self):
        return self._response_schema(
            next_states={"select_line", "set_line_destination"}
        )

    def set_destination(self):
        return self._response_schema(
            next_states={"select_line", "set_line_destination", "zero_check"}
        )

    def is_zero(self):
        return self._response_schema(next_states={"select_line"})

    def stock_issue(self):
        return self._response_schema(
            next_states={"select_line", "set_line_destination"}
        )

    def change_pack_lot(self):
        return self._response_schema(
            next_states={"change_pack_lot", "set_line_destination", "select_line"}
        )

    def prepare_unload(self):
        return self._response_schema(
            next_states={
                "unload_all",
                "unload_single",
                "unload_set_destination",
                "select_line",
            }
        )

    def set_destination_all(self):
        return self._response_schema(next_states={"unload_all", "select_line"})

    def unload_split(self):
        return self._response_schema(
            next_states={"unload_single", "unload_set_destination", "select_line"}
        )

    def unload_scan_pack(self):
        return self._response_schema(
            next_states={
                "unload_single",
                "unload_set_destination",
                "select_line",
                "start",
            }
        )

    def unload_set_destination(self):
        return self._response_schema(
            next_states={"unload_single", "unload_set_destination", "select_line"}
        )

    @property
    def _schema_for_select_zone(self):
        zone_schema = self.schemas.location()
        picking_type_schema = self.schemas.picking_type()
        picking_type_schema.update(self._schema_for_zone_line_counters)
        zone_schema["operation_types"] = self.schemas._schema_list_of(
            picking_type_schema
        )
        zone_schema = {
            "zones": self.schemas._schema_list_of(zone_schema),
        }
        return zone_schema

    @property
    def _schema_for_zone_line_counters(self):
        return {
            "lines_count": {"type": "float", "required": True},
            "picking_count": {"type": "float", "required": True},
            "priority_lines_count": {"type": "float", "required": True},
            "priority_picking_count": {"type": "float", "required": True},
        }

    @property
    def _schema_for_select_picking_type(self):
        picking_type = self.schemas.picking_type()
        picking_type.update(self._schema_for_zone_line_counters)
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_types": self.schemas._schema_list_of(picking_type),
        }
        return schema

    @property
    def _schema_for_move_line(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_type": self.schemas._schema_dict_of(self.schemas.picking_type()),
            "move_line": self.schemas._schema_dict_of(
                self.schemas.move_line(with_picking=True)
            ),
            "confirmation_required": {
                "type": "boolean",
                "nullable": True,
                "required": False,
            },
        }
        return schema

    @property
    def _schema_for_move_lines(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_type": self.schemas._schema_dict_of(self.schemas.picking_type()),
            "move_lines": self.schemas._schema_list_of(
                self.schemas.move_line(with_picking=True)
            ),
            "confirmation_required": {
                "type": "boolean",
                "nullable": True,
                "required": False,
            },
        }
        return schema

    @property
    def _schema_for_move_lines_empty_location(self):
        schema = self._schema_for_move_lines
        schema["move_lines"]["schema"]["schema"]["location_will_be_empty"] = {
            "type": "boolean",
            "nullable": False,
            "required": True,
        }
        return schema

    @property
    def _schema_for_zero_check(self):
        schema = {
            "zone_location": self.schemas._schema_dict_of(self.schemas.location()),
            "picking_type": self.schemas._schema_dict_of(self.schemas.picking_type()),
            "location": self.schemas._schema_dict_of(self.schemas.location()),
        }
        return schema
