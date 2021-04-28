# Copyright 2020-2021 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import functools
from collections import defaultdict

from odoo.fields import first
from odoo.tools.float_utils import float_compare, float_is_zero

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from ..utils import to_float


class ZonePicking(Component):
    """
    Methods for the Zone Picking Process

    Zone picking of move lines.

    You will find a sequence diagram describing states and endpoints
    relationships [here](../docs/zone_picking_diag_seq.png).
    Keep [the sequence diagram](../docs/zone_picking_diag_seq.plantuml)
    up-to-date if you change endpoints.

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
       * package, if it is linked to a move line. If the package is not linked
         to an existing move line but can be a replacement for one, the view is
         updated to show only the fitting move lines. And the user can confirm
         the change of package by scanning it a second time.
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

    @property
    def _validation_rules(self):
        return super()._validation_rules + (
            # rule to apply, active flag handler
            (self.ZONE_LOCATION_ID_HEADER_RULE, self._requires_header_zone_picking),
            (self.PICKING_TYPE_ID_HEADER_RULE, self._requires_header_zone_picking),
            (self.LINES_ORDER_HEADER_RULE, self._requires_header_zone_picking),
        )

    def _requires_header_zone_picking(self, request, method):
        # TODO: maybe we should have a decorator?
        return method not in ("select_zone", "scan_location")

    ZONE_LOCATION_ID_HEADER_RULE = (
        # header name, coerce func, ctx handler, mandatory
        "HTTP_SERVICE_CTX_ZONE_LOCATION_ID",
        int,
        "_work_ctx_get_zone_location_id",
        True,
    )
    PICKING_TYPE_ID_HEADER_RULE = (
        # header name, coerce func, ctx handler, mandatory
        "HTTP_SERVICE_CTX_PICKING_TYPE_ID",
        int,
        "_work_ctx_get_picking_type_id",
        True,
    )
    LINES_ORDER_HEADER_RULE = (
        # header name, coerce func, ctx handler, mandatory
        "HTTP_SERVICE_CTX_LINES_ORDER",
        str,
        "_work_ctx_get_lines_order",
        True,
    )

    def _work_ctx_get_zone_location_id(self, rec_id):
        return (
            "current_zone_location",
            self.env["stock.location"].browse(rec_id).exists(),
        )

    def _work_ctx_get_picking_type_id(self, rec_id):
        return (
            "current_picking_type",
            self.env["stock.picking.type"].browse(rec_id).exists(),
        )

    def _work_ctx_get_lines_order(self, order):
        return "current_lines_order", order

    @property
    def zone_location(self):
        return self.work.current_zone_location

    @property
    def picking_type(self):
        return getattr(self.work, "current_picking_type", None)

    @property
    def lines_order(self):
        return getattr(self.work, "current_lines_order", "priority")

    def _pick_pack_same_time(self):
        return self.work.menu.pick_pack_same_time

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
        self, move_lines, message=None, popup=None, confirmation_required=False
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_lines(move_lines)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="select_line", data=data, message=message, popup=popup,
        )

    def _response_for_set_line_destination(
        self, move_line, message=None, confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_line(move_line)
        data["confirmation_required"] = confirmation_required
        return self._response(
            next_state="set_line_destination", data=data, message=message
        )

    def _response_for_zero_check(self, move_line, message=None):
        data = self._data_for_location(move_line.location_id)
        data["move_line"] = self.data.move_line(move_line)
        return self._response(next_state="zero_check", data=data, message=message,)

    def _response_for_change_pack_lot(self, move_line, message=None):
        return self._response(
            next_state="change_pack_lot",
            data=self._data_for_move_line(move_line),
            message=message,
        )

    def _response_for_unload_all(
        self, move_lines, message=None, confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_lines(move_lines)
        data["confirmation_required"] = confirmation_required
        return self._response(next_state="unload_all", data=data, message=message)

    def _response_for_unload_single(self, move_line, message=None, popup=None):
        buffer_lines = self._find_buffer_move_lines()
        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(buffer_lines)
        return self._response(
            next_state="unload_single",
            data=self._data_for_move_line(move_line),
            message=message,
            popup=popup or completion_info_popup,
        )

    def _response_for_unload_set_destination(
        self, move_line, message=None, confirmation_required=False,
    ):
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        data = self._data_for_move_line(move_line)
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
            counters = self._counters_for_zone_lines(zone_lines)
            datum.update(counters)
        return data

    def _counters_for_zone_lines(self, zone_lines):
        return self.search_move_line.counters_for_lines(zone_lines)

    def _picking_type_zone_lines(self, zone_location, picking_type):
        return self.search_move_line.search_move_lines_by_location(
            zone_location, picking_type=picking_type
        )

    def _data_for_move_line(self, move_line, zone_location=None, picking_type=None):
        zone_location = zone_location or self.zone_location
        picking_type = picking_type or self.picking_type
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "move_line": self.data.move_line(move_line, with_picking=True),
        }

    def _data_for_move_lines(self, move_lines, zone_location=None, picking_type=None):
        zone_location = zone_location or self.zone_location
        picking_type = picking_type or self.picking_type
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

    def _data_for_location(self, location, zone_location=None, picking_type=None):
        zone_location = zone_location or self.zone_location
        picking_type = picking_type or self.picking_type
        return {
            "zone_location": self.data.location(zone_location),
            "picking_type": self.data.picking_type(picking_type),
            "location": self.data.location(location),
        }

    def _zone_lines(self, zones):
        return self._find_location_move_lines(zones)

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
            zone_lines = self._zone_lines(zone)
            if not zone_lines:
                continue
            lines_by_op_type = defaultdict(list)
            for line in zone_lines:
                lines_by_op_type[line.picking_id.picking_type_id].append(line)

            zone_data["operation_types"] = []
            zone_counters = defaultdict(int)
            for picking_type, lines in lines_by_op_type.items():
                op_type_data = self.data.picking_type(picking_type)
                counters = self._counters_for_zone_lines(lines)
                op_type_data.update(counters)
                zone_data["operation_types"].append(op_type_data)
                for k, v in counters.items():
                    zone_counters[k] += v
            zone_data.update(zone_counters)
            res.append(zone_data)
        return res

    def _find_location_move_lines(
        self,
        locations=None,
        picking_type=None,
        package=None,
        product=None,
        lot=None,
        match_user=False,
    ):
        """Find lines that potentially need work in given locations."""
        return self.search_move_line.search_move_lines_by_location(
            locations or self.zone_location,
            picking_type=picking_type or self.picking_type,
            order=self.lines_order,
            package=package,
            product=product,
            lot=lot,
            match_user=match_user,
        )

    def _find_buffer_move_lines_domain(self, dest_package=None):
        domain = [
            ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ("qty_done", ">", 0),
            ("state", "not in", ("cancel", "done")),
            ("result_package_id", "!=", False),
            ("shopfloor_user_id", "=", self.env.user.id),
        ]
        if dest_package:
            domain.append(("result_package_id", "=", dest_package.id))
        return domain

    def _find_buffer_move_lines(self, dest_package=None):
        """Find lines that belongs to the operator's buffer and return them
        grouped by destination package.
        """
        domain = self._find_buffer_move_lines_domain(dest_package)
        return (
            self.env["stock.move.line"]
            .search(domain)
            .sorted(self.search_move_line._sort_key_move_lines(self.lines_order))
        )

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
        search = self._actions_for("search")
        zone_location = search.location_from_scan(barcode)
        if not zone_location:
            return self._response_for_start(message=self.msg_store.no_location_found())
        if not self.is_src_location_valid(zone_location):
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

    def list_move_lines(self):
        """List all move lines to pick, sorted

        Transitions:
        * select_line: show the list of move lines
        """
        return self._list_move_lines(self.zone_location)

    def _list_move_lines(self, location):
        move_lines = self._find_location_move_lines(location)
        return self._response_for_select_line(move_lines)

    def _scan_source_location(self, barcode, confirmation=False):
        """Search a location and find available lines into it.
        """
        response = None
        message = None
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if not location:
            return response, message

        if not location.is_sublocation_of(self.zone_location):
            response = self._response_for_start(
                message=self.msg_store.location_not_allowed()
            )
            return response, message

        product, lot, package = self._find_product_in_location(location)
        if len(product) > 1 or len(lot) > 1 or len(package) > 1:
            response = self._list_move_lines(location)
            message = self.msg_store.several_products_in_location(location)
            return response, message

        move_lines = self._find_location_move_lines(
            location, product=product, lot=lot, package=package, match_user=True,
        )
        if move_lines:
            response = self._response_for_set_line_destination(first(move_lines))
        else:
            # if no move line, narrow the list of move lines on the scanned location
            response = self._list_move_lines(location)
            message = self.msg_store.location_empty(location)
        return response, message

    def _find_product_in_location(self, location):
        """Find a prooduct in stock in given location move line in the location.
        """
        quants = self.env["stock.quant"].search([("location_id", "=", location.id)])
        product = quants.product_id
        lot = quants.lot_id
        package = quants.package_id
        return product, lot, package

    def _scan_source_package(self, barcode, confirmation=False):
        """Search a package and find available lines for it.

        Fist search for lines that have the specific package.
        If none are found search for lines whose package could be replaced
        by the one selected and in that case ask for confirmation.
        """
        message = None
        response = None
        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if not package:
            return response, message
        move_lines = self._find_location_move_lines(package=package)
        if move_lines:
            response = self._response_for_set_line_destination(first(move_lines))
            return response, message
        pack_location = package.location_id
        if pack_location and pack_location.is_sublocation_of(self.zone_location):
            # Check if the package selected can be a substitute on a move line
            move_lines = self._find_location_move_lines(
                locations=pack_location,
                product=package.product_packaging_id.product_id,
            )
        if move_lines:
            if not confirmation:
                message = self.msg_store.package_different_change()
                response = self._response_for_select_line(
                    move_lines, message, confirmation_required=True
                )
            else:
                change_package_lot = self._actions_for("change.package.lot")
                response = change_package_lot.change_package(
                    first(move_lines),
                    package,
                    self._response_for_set_line_destination,
                    self._response_for_change_pack_lot,
                )
        else:
            response = self._list_move_lines(self.zone_location)
            message = self.msg_store.package_has_no_product_to_take(barcode)
        return response, message

    def _scan_source_product(self, barcode, confirmation=False):
        """Search a product and find available lines for it.
        """
        message = None
        response = None
        search = self._actions_for("search")
        product = search.product_from_scan(barcode)
        if not product:
            return response, message
        move_lines = self._find_location_move_lines(product=product)
        if move_lines:
            response = self._response_for_set_line_destination(first(move_lines))
        else:
            response = self._list_move_lines(self.zone_location)
            message = self.msg_store.product_not_found()
        return response, message

    def _scan_source_lot(self, barcode, confirmation=False):
        """Search a lot and find available lines for it.
        """
        message = None
        response = None
        search = self._actions_for("search")
        lot = search.lot_from_scan(barcode)
        if not lot:
            return response, message
        move_lines = self._find_location_move_lines(lot=lot)
        if move_lines:
            response = self._response_for_set_line_destination(first(move_lines))
        else:
            response = self._list_move_lines(self.zone_location)
            message = self.msg_store.lot_not_found()
        return response, message

    def scan_source(self, barcode, confirmation=False):
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

        # select corresponding move line from barcode (location, package, product, lot)
        handlers = (
            # search by location 1st
            self._scan_source_location,
            # then by package
            self._scan_source_package,
            # then by product
            self._scan_source_product,
            # then by lot
            self._scan_source_lot,
        )
        for handler in handlers:
            response, message = handler(barcode, confirmation=confirmation)
            if response:
                return self._response(base_response=response, message=message)
        response = self.list_move_lines()
        return self._response(
            base_response=response, message=self.msg_store.barcode_not_found()
        )

    def _set_destination_location(self, move_line, quantity, confirmation, location):
        location_changed = False
        response = None

        # A valid location is a sub-location of the original destination, or a
        # any sub-location of the picking type's default destination location
        # if `confirmation is True
        # Ask confirmation to the user if the scanned location is not in the
        # expected ones but is valid (in picking type's default destination)
        if not self.is_dest_location_valid(move_line.move_id, location):
            response = self._response_for_set_line_destination(
                move_line, message=self.msg_store.dest_location_not_allowed(),
            )
            return (location_changed, response)

        if not confirmation and self.is_dest_location_to_confirm(
            move_line.location_dest_id, location
        ):
            response = self._response_for_set_line_destination(
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
                move_line, message=self.msg_store.dest_package_required(),
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
        stock = self._actions_for("stock")
        stock.validate_moves(move_line.move_id)
        location_changed = True
        # Zero check
        zero_check = self.picking_type.shopfloor_zero_check
        if zero_check and move_line.location_id.planned_qty_in_location_is_empty():
            response = self._response_for_zero_check(move_line)
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

    def _set_destination_package(self, move_line, quantity, package):
        package_changed = False
        response = None
        # A valid package is:
        # * an empty package
        # * not used as destination for another move line
        if not self._is_package_empty(package):
            response = self._response_for_set_line_destination(
                move_line, message=self.msg_store.package_not_empty(package),
            )
            return (package_changed, response)
        if self._is_package_already_used(package):
            response = self._response_for_set_line_destination(
                move_line, message=self.msg_store.package_already_used(package),
            )
            return (package_changed, response)
        # the quantity done is set to the passed quantity
        # but if we move a partial qty, we need to split the move line
        compare = self._move_line_compare_qty(move_line, quantity)
        qty_lesser = compare == -1
        qty_greater = compare == 1
        if qty_greater:
            response = self._response_for_set_line_destination(
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
        self._set_move_line_as_done(move_line, quantity, package)
        package_changed = True
        # Zero check
        zero_check = self.picking_type.shopfloor_zero_check
        if zero_check and move_line.location_id.planned_qty_in_location_is_empty():
            response = self._response_for_zero_check(move_line)
        return (package_changed, response)

    def _set_move_line_as_done(self, move_line, quantity, package, user=None):
        move_line.qty_done = quantity
        # destination package is set to the scanned one
        move_line.result_package_id = package
        # the field ``shopfloor_user_id`` is updated with the current user
        move_line.shopfloor_user_id = user or self.env.user

    # flake8: noqa: C901
    def set_destination(
        self, move_line_id, barcode, quantity, confirmation=False,
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
        * set_line_destination+confirmation_required: the scanned location is not
          in the expected one but is valid (in picking type's default destination)
        """
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())

        pkg_moved = False
        search = self._actions_for("search")
        accept_only_package = not self._move_line_full_qty(move_line, quantity)

        extra_message = ""
        if not accept_only_package:
            # When the barcode is a location
            location = search.location_from_scan(barcode)
            if location:
                if self._pick_pack_same_time():
                    (
                        good_for_packing,
                        message,
                    ) = self._handle_pick_pack_same_time_for_location(move_line)
                    # TODO: we should append the msg instead.
                    # To achieve this, we should refactor `response.message` to a list
                    # or, to no break backward compat, we could add `extra_messages`
                    # to allow backend to send a main message and N additional messages.
                    extra_message = message
                    if not good_for_packing:
                        return self._response_for_set_line_destination(
                            move_line, message=message
                        )
                pkg_moved, response = self._set_destination_location(
                    move_line, quantity, confirmation, location,
                )
                if response:
                    if extra_message:
                        if response.get("message"):
                            response["message"]["body"] += "\n" + extra_message["body"]
                        else:
                            response["message"] = extra_message
                    return response

        # When the barcode is a package
        package = search.package_from_scan(barcode)
        if package:
            if self._pick_pack_same_time():
                (
                    good_for_packing,
                    message,
                ) = self._handle_pick_pack_same_time_for_package(move_line, package)
                if not good_for_packing:
                    return self._response_for_set_line_destination(
                        move_line, message=message
                    )
            location = move_line.location_dest_id
            pkg_moved, response = self._set_destination_package(
                move_line, quantity, package
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
            return self._response_for_set_line_destination(move_line, message=message)

        if pkg_moved:
            message = self.msg_store.confirm_pack_moved()
            if extra_message:
                message["body"] += "\n" + extra_message["body"]

        # Process the next line
        response = self.list_move_lines()
        return self._response(base_response=response, message=message)

    def _handle_pick_pack_same_time_for_location(self, move_line):
        """Automatically put product in carrier-specific package.

        :param move_line: current move line to process
        :return: tuple like ($succes_flag, $success_or_failure_message)
        """
        good_for_packing = False
        message = ""
        picking = move_line.picking_id
        carrier = picking.ship_carrier_id or picking.carrier_id
        if carrier:
            actions = self._actions_for("packaging")
            pkg = actions.create_delivery_package(carrier)
            move_line.write({"result_package_id": pkg.id})
            message = self.msg_store.goods_packed_in(pkg)
            good_for_packing = True
        else:
            message = self.msg_store.picking_without_carrier_cannot_pack(picking)
        return good_for_packing, message

    def _handle_pick_pack_same_time_for_package(self, move_line, package):
        """Validate package for packing at the same time.

        :param move_line: current move line to process
        :param package: package to validate
        :return: tuple like ($succes_flag, $success_or_failure_message)
        """
        good_for_packing = False
        message = None
        picking = move_line.picking_id
        carrier = picking.ship_carrier_id or picking.carrier_id
        if carrier:
            actions = self._actions_for("packaging")
            if actions.packaging_valid_for_carrier(package.packaging_id, carrier):
                good_for_packing = True
            else:
                message = self.msg_store.packaging_invalid_for_carrier(
                    package.packaging_id, carrier
                )
        else:
            message = self.msg_store.picking_without_carrier_cannot_pack(picking)
        return good_for_packing, message

    def is_zero(self, move_line_id, zero):
        """Confirm or not if the source location of a move has zero qty

        If the user confirms there is zero quantity, it means the stock was
        correct and there is nothing to do. If the user says "no", a draft
        empty inventory is created for the product (with lot if tracked).

        Transitions:
        * select_line: whether the user confirms or not the location is empty,
          go back to the picking of lines
        """
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        if not zero:
            inventory = self._actions_for("inventory")
            inventory.create_draft_check_empty(
                move_line.location_id,
                # FIXME as zero_check is done on the whole location, we should
                # create an inventory on it without the product critera
                # => the same applies on "Cluster Picking" scenario
                # move_line.product_id,
                move_line.product_id.browse(),  # HACK send an empty recordset
                ref=self.picking_type.name,
            )
        return self.list_move_lines()

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

    def stock_issue(self, move_line_id):
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
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        inventory = self._actions_for("inventory")
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
            return self._response_for_set_line_destination(move.move_line_ids[0])
        return self.list_move_lines()

    def change_pack_lot(self, move_line_id, barcode):
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
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        search = self._actions_for("search")
        # pre-configured callable used to generate the response as the
        # change.package.lot component is not aware of the needed response type
        # and related parameters for zone picking scenario
        response_ok_func = functools.partial(self._response_for_set_line_destination)
        response_error_func = functools.partial(self._response_for_change_pack_lot)
        response = None
        change_package_lot = self._actions_for("change.package.lot")
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
            move_line, message=self.msg_store.no_package_or_lot_for_barcode(barcode),
        )

    def prepare_unload(self):
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
        move_lines = self._find_buffer_move_lines()
        location_dest = move_lines.mapped("location_dest_id")
        if len(move_lines) == 1:
            return self._response_for_unload_set_destination(move_lines)
        elif len(move_lines) > 1 and len(location_dest) == 1:
            return self._response_for_unload_all(move_lines)
        elif len(move_lines) > 1 and len(location_dest) > 1:
            return self._response_for_unload_single(first(move_lines))
        return self.list_move_lines()

    def _set_destination_all_response(self, buffer_lines, message=None):
        if buffer_lines:
            return self._response_for_unload_all(buffer_lines, message=message)
        move_lines = self._find_location_move_lines()
        if move_lines:
            return self._response_for_select_line(move_lines, message=message)
        return self._response_for_start(message=message)

    def set_destination_all(self, barcode, confirmation=False):
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
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        message = None
        buffer_lines = self._find_buffer_move_lines()
        if location:
            error = None
            location_dest = buffer_lines.mapped("location_dest_id")
            # check if move lines share the same destination
            if len(location_dest) != 1:
                error = self.msg_store.lines_different_dest_location()
            # check if the scanned location is allowed
            moves = buffer_lines.mapped("move_id")
            if not self.is_dest_location_valid(moves, location):
                error = self.msg_store.location_not_allowed()
            if error:
                return self._set_destination_all_response(buffer_lines, message=error)
            # check if the destination location is not the expected one
            #   - OK if the scanned destination is a child of the current
            #     destination set on buffer lines
            #   - To confirm if the scanned destination is not a child of the
            #     current destination set on buffer lines
            if not confirmation and self.is_dest_location_to_confirm(
                buffer_lines.location_dest_id, location
            ):
                return self._response_for_unload_all(
                    buffer_lines,
                    message=self.msg_store.confirm_location_changed(
                        first(buffer_lines.location_dest_id), location
                    ),
                    confirmation_required=True,
                )
            # the scanned location is still valid, use it
            self._write_destination_on_lines(buffer_lines, location)
            # set lines to done + refresh buffer lines (should be empty)
            # split move lines to a backorder move
            # if quantity is not fully satisfied
            # TODO: update tests
            for move in moves:
                move.split_other_move_lines(buffer_lines & move.move_line_ids)
            stock = self._actions_for("stock")
            stock.validate_moves(moves)
            message = self.msg_store.buffer_complete()
            buffer_lines = self._find_buffer_move_lines()
        else:
            message = self.msg_store.no_location_found()
        return self._set_destination_all_response(buffer_lines, message=message)

    def _write_destination_on_lines(self, lines, location):
        self._lock_lines(lines)
        lines.location_dest_id = location
        lines.package_level_id.location_dest_id = location

    def unload_split(self):
        """Indicates that now the buffer must be treated line per line

        Called from a button, users decides to handle destinations one by one.
        Even if the move lines to unload all have the same destination.

        Look in ``prepare_unload`` for the definition of the buffer.

        Transitions:
        * unload_single: more than one remaining line in the buffer
        * unload_set_destination: there is only one remaining line in the buffer
        * select_line: no remaining move lines in buffer
        """
        buffer_lines = self._find_buffer_move_lines()
        # more than one remaining move line in the buffer
        if len(buffer_lines) > 1:
            return self._response_for_unload_single(first(buffer_lines))
        # only one move line to process in the buffer
        elif len(buffer_lines) == 1:
            return self._response_for_unload_set_destination(first(buffer_lines))
        # no remaining move lines in buffer
        move_lines = self._find_location_move_lines()
        return self._response_for_select_line(
            move_lines, message=self.msg_store.buffer_complete(),
        )

    def _unload_response(self, unload_single_message=None):
        """Prepare the right response depending on the move lines to process."""
        # if there are still move lines to process from the buffer
        move_lines = self._find_buffer_move_lines()
        if move_lines:
            return self._response_for_unload_single(
                first(move_lines), message=unload_single_message,
            )
        # if there are still move lines to process from the picking type
        #   => buffer complete!
        move_lines = self._find_location_move_lines()
        if move_lines:
            return self._response_for_select_line(
                move_lines, message=self.msg_store.buffer_complete(),
            )
        # no more move lines to process from the current picking type
        #   => picking type complete!
        return self._response_for_start(
            message=self.msg_store.picking_type_complete(self.picking_type)
        )

    def unload_scan_pack(self, package_id, barcode):
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
        package = self.env["stock.quant.package"].browse(package_id)
        if not package.exists():
            return self._unload_response(
                unload_single_message=self.msg_store.record_not_found(),
            )
        search = self._actions_for("search")
        scanned_package = search.package_from_scan(barcode)
        # the scanned barcode matches the package
        if scanned_package == package:
            move_lines = self._find_buffer_move_lines(dest_package=scanned_package)
            if move_lines:
                return self._response_for_unload_set_destination(first(move_lines))
        return self._unload_response(
            unload_single_message=self.msg_store.barcode_no_match(package.name),
        )

    def _lock_lines(self, lines):
        """Lock move lines"""
        sql = "SELECT id FROM %s WHERE ID IN %%s FOR UPDATE" % lines._table
        self.env.cr.execute(sql, (tuple(lines.ids),), log_exceptions=False)

    def unload_set_destination(self, package_id, barcode, confirmation=False):
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
        package = self.env["stock.quant.package"].browse(package_id)
        buffer_lines = self._find_buffer_move_lines(dest_package=package)
        if not package.exists() or not buffer_lines:
            move_lines = self._find_location_move_lines()
            return self._response_for_select_line(
                move_lines, message=self.msg_store.record_not_found(),
            )
        search = self._actions_for("search")
        location = search.location_from_scan(barcode)
        if location:
            moves = buffer_lines.mapped("move_id")
            if not self.is_dest_location_valid(moves, location):
                return self._response_for_unload_set_destination(
                    first(buffer_lines),
                    message=self.msg_store.dest_location_not_allowed(),
                )
            # check if the destination location is not the expected one
            #   - OK if the scanned destination is a child of the current
            #     destination set on buffer lines
            #   - To confirm if the scanned destination is not a child of the
            #     current destination set on buffer lines
            if not confirmation and self.is_dest_location_to_confirm(
                buffer_lines.location_dest_id, location
            ):
                return self._response_for_unload_set_destination(
                    first(buffer_lines),
                    message=self.msg_store.confirm_location_changed(
                        first(buffer_lines.location_dest_id), location
                    ),
                    confirmation_required=True,
                )
            # the scanned location is valid, use it
            self._write_destination_on_lines(buffer_lines, location)
            # set lines to done + refresh buffer lines (should be empty)
            # split move lines to a backorder move
            # if quantity is not fully satisfied
            for move in moves:
                move.split_other_move_lines(buffer_lines & move.move_line_ids)

            stock = self._actions_for("stock")
            stock.validate_moves(moves)
            buffer_lines = self._find_buffer_move_lines()

            if buffer_lines:
                # TODO: return success message if line has been processed
                return self._response_for_unload_single(first(buffer_lines))
            move_lines = self._find_location_move_lines()
            if move_lines:
                return self._response_for_select_line(
                    move_lines, message=self.msg_store.buffer_complete(),
                )
            return self._response_for_start(
                message=self.msg_store.picking_type_complete(self.picking_type)
            )
        # TODO: when we have no lines here
        # we should not redirect to `unload_set_destination`
        # because we'll have nothing to display (currently the UI is broken).
        return self._response_for_unload_set_destination(
            first(buffer_lines), message=self.msg_store.no_location_found(),
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
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def scan_source(self):
        return {
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def set_destination(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def is_zero(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "zero": {"coerce": to_bool, "required": True, "type": "boolean"},
        }

    def stock_issue(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def change_pack_lot(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def prepare_unload(self):
        return {}

    def set_destination_all(self):
        return {
            "barcode": {"required": False, "nullable": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def unload_split(self):
        return {}

    def unload_scan_pack(self):
        return {
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": False, "nullable": True, "type": "string"},
        }

    def unload_set_destination(self):
        return {
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
        zone_schema.update(self._schema_for_zone_line_counters)
        zone_schema = {
            "zones": self.schemas._schema_list_of(zone_schema),
        }
        return zone_schema

    @property
    def _schema_for_zone_line_counters(self):
        return self.schemas.move_lines_counters()

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
            "move_line": self.schemas._schema_dict_of(self.schemas.move_line()),
        }
        return schema
