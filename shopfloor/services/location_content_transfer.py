# Copyright 2020-2021 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020-2022 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _
from odoo.fields import first

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from ..utils import to_float

# NOTE for the implementation: share several similarities with the "cluster
# picking" scenario


# TODO add picking and package content in package level?


class LocationContentTransfer(Component):
    """
    Methods for the Location Content Transfer Process

    Move the full content of a location to one or more locations.

    Generally used to move a pallet with multiple boxes to either:

    * 1 destination location, unloading the full pallet
    * To multiple destination locations, unloading one product/lot per
      locations
    * To multiple destination locations, unloading one product/lot per
      locations and then unloading all remaining product/lot to a single final
      destination

    The move lines must exist beforehand, the workflow only moves them.

    Expected:

    * All move lines and package level have a destination set, and are done.

    2 complementary actions are possible on the screens allowing to move a line:

    * Declare a stock out for a product or package (nothing found in the
      location)
    * Skip to the next line (will be asked again at the end)

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.location.content.transfer"
    _usage = "location_content_transfer"
    _description = __doc__

    _advisory_lock_find_work = "location_content_transfer_find_work"

    def _response_for_start(self, message=None, popup=None):
        """Transition to the 'start' or 'get_work' state

        The switch to 'get_work' is done if the option is enabled on the scenario
        """
        if self.work.menu.allow_get_work:
            return self._response(
                next_state="get_work", data={}, message=message, popup=popup
            )
        return self._response(next_state="scan_location", message=message, popup=popup)

    def _response_for_scan_location(self, location=None, message=None):
        """Transition to the 'scan_location' state

        If location is set, the client will display information on that location
        and only accept this specific location to be scanned.
        """
        data = {}
        if location:
            data["location"] = self.data.location(location)
        return self._response(
            next_state="scan_location",
            data=data,
            message=message,
        )

    def _response_for_scan_destination_all(
        self, pickings, message=None, confirmation_required=None
    ):
        """Transition to the 'scan_destination_all' state

        The client screen shows a summary of all the lines and packages
        to move to a single destination.

        If `confirmation_required` is set,
        the client will ask to scan again the destination
        """
        data = self._data_content_all_for_location(pickings=pickings)
        data["confirmation_required"] = confirmation_required
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        return self._response(
            next_state="scan_destination_all", data=data, message=message
        )

    def _response_for_start_single(self, pickings, message=None, popup=None):
        """Transition to the 'start_single' state

        The client screen shows details of the package level or move line to move.
        """
        location = pickings.mapped("location_id")
        next_content = self._next_content(pickings)
        if not next_content:
            # TODO test (no more lines)
            return self._response_for_start(message=message, popup=popup)
        return self._response(
            next_state="start_single",
            data=self._data_content_line_for_location(location, next_content),
            message=message,
            popup=popup,
        )

    def _response_for_scan_destination(
        self, location, next_content, message=None, confirmation_required=None
    ):
        """Transition to the 'scan_destination' state

        The client screen shows details of the package level or move line to move.
        """
        data = self._data_content_line_for_location(location, next_content)
        data["confirmation_required"] = confirmation_required
        if confirmation_required and not message:
            message = self.msg_store.need_confirmation()
        return self._response(next_state="scan_destination", data=data, message=message)

    def _data_content_all_for_location(self, pickings):
        sorter = self._actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        lines = sorter.move_lines()
        package_levels = sorter.package_levels()
        location = pickings.mapped("move_line_ids.location_id")
        assert len(location) == 1, "There should be only one src location at this stage"
        return {
            "location": self.data.location(location),
            "move_lines": self.data.move_lines(lines),
            "package_levels": self.data.package_levels(package_levels),
        }

    def _data_content_line_for_location(self, location, next_content):
        assert next_content._name in ("stock.move.line", "stock.package_level")
        line_data = (
            self.data.move_line(next_content)
            if next_content._name == "stock.move.line"
            else None
        )
        level_data = (
            self.data.package_level(next_content)
            if next_content._name == "stock.package_level"
            else None
        )
        return {"move_line": line_data, "package_level": level_data}

    def _next_content(self, pickings):
        sorter = self._actions_for("location_content_transfer.sorter")
        sorter.feed_pickings(pickings)
        try:
            next_content = next(sorter)
        except StopIteration:
            # TODO set picking to done
            return None
        return next_content

    def _router_single_or_all_destination(self, pickings, message=None):
        location_dest = pickings.mapped("move_line_ids.location_dest_id")
        location_src = pickings.mapped("move_line_ids.location_id")
        if len(location_dest) == len(location_src) == 1:
            return self._response_for_scan_destination_all(pickings, message=message)
        else:
            return self._response_for_start_single(pickings, message=message)

    def _domain_recover_pickings(self):
        return [
            ("user_id", "=", self.env.uid),
            ("state", "=", "assigned"),
            ("picking_type_id", "in", self.picking_types.ids),
        ]

    def _search_recover_pickings(self):
        candidate_pickings = self.env["stock.picking"].search(
            self._domain_recover_pickings()
        )
        started_pickings = candidate_pickings.filtered(
            lambda picking: any(line.qty_done for line in picking.move_line_ids)
        )
        return started_pickings

    def _recover_started_picking(self):
        """Get the next response if the user has work in progress."""
        started_pickings = self._search_recover_pickings()
        if not started_pickings:
            return False
        return self._router_single_or_all_destination(
            started_pickings, message=self.msg_store.recovered_previous_session()
        )

    def start_or_recover(self):
        """Start a new session or recover an existing one

        If the current user had transfers in progress in this scenario
        and reopen the menu, we want to directly reopen the screens to choose
        destinations. Otherwise, we go to the "start" state.
        """
        response = self._recover_started_picking()
        return response or self._response_for_start()

    def _create_moves_from_location(self, location):
        # get all quants from the scanned location
        quants = self.env["stock.quant"].search(
            [("location_id", "=", location.id), ("quantity", ">", 0)]
        )
        # create moves for each quant
        picking_type = self.picking_types
        move_vals_list = []
        for quant in quants:
            move_vals_list.append(
                {
                    "name": quant.product_id.name,
                    "company_id": picking_type.company_id.id,
                    "product_id": quant.product_id.id,
                    "product_uom": quant.product_uom_id.id,
                    "product_uom_qty": quant.quantity,
                    "location_id": location.id,
                    "location_dest_id": picking_type.default_location_dest_id.id,
                    "origin": self.work.menu.name,
                    "picking_type_id": picking_type.id,
                }
            )
        return self.env["stock.move"].create(move_vals_list)

    def _find_location_to_work_from(self):
        move_lines = self.search_move_line.search_move_lines(match_user=True)
        return first(move_lines).location_id

    def _select_move_lines_first_location(self, move_lines):
        location = first(move_lines).location_id
        return move_lines.filtered(lambda line: line.location_id == location)

    def find_work(self):
        """Find the next location to work from, for a user.

        First recover any started pickings.
        The find the first move line from the oldest transfer that can be worked on.
        Mark all move lines on that location as picked.
        And ask the user to confirm.

        Transitions:
        * start: no work found
        * scan_location: with the location to work form for confirmation
        """
        response = self._recover_started_picking()
        if response:
            return response

        self._actions_for("lock").advisory(self._advisory_lock_find_work)
        move_lines = self.search_move_line.search_move_lines(match_user=True)
        if not move_lines:
            return self._response_for_start(message=self.msg_store.no_work_found())
        move_lines = self._select_move_lines_first_location(move_lines)
        stock = self._actions_for("stock")
        stock.mark_move_line_as_picked(move_lines, quantity=0)
        return self._response_for_scan_location(location=move_lines.location_id)

    def _find_move_lines_to_cancel_work(self, location):
        unreserve = self._actions_for("stock.unreserve")
        return self.env["stock.move.line"].search(
            unreserve._find_location_all_move_lines_domain(location)
        )

    def _move_lines_cancel_work(self, move_lines):
        move_lines.write({"shopfloor_user_id": False})
        move_lines.mapped("picking_id").write({"user_id": False})
        stock = self._actions_for("stock")
        stock.unmark_move_line_as_picked(move_lines)

    def cancel_work(self, location_id):
        """Cancel work marked as picked by the user.

        Transitions:
        * start:
        """
        location = self.env["stock.location"].browse(location_id)
        if not location:
            return self._response_for_start(message=self.msg_store.location_not_found())

        move_lines = self._find_move_lines_to_cancel_work(location)
        self._move_lines_cancel_work(move_lines)
        return self._response_for_start()

    def scan_location(self, barcode):  # noqa: C901
        """Scan start location

        Called at the beginning at the workflow to select the location from which
        we want to move the content.

        All the move lines and package levels must have the same picking type.

        If the scanned location has no move lines, new move lines to move the
        whole content of the location are created if:

        * the menu has the option "Allow to create move(s)"
        * the menu is linked to only one picking type.

        When move lines and package levels have different destinations, the
        first line without package level or package level is sent to the client.

        The selected move lines to process are bound to the current operator,
        this will allow another operator to find unprocessed lines in parallel
        and not overlap with current ones.

        Transitions:
        * start: location not found, ...
        * scan_destination_all: if the destination of all the lines and package
        levels have the same destination
        * start_single: if any line or package level has a different destination
        """
        location = self._actions_for("search").location_from_scan(barcode)
        if not location:
            return self._response_for_start(message=self.msg_store.barcode_not_found())

        if not self.is_src_location_valid(location):
            return self._response_for_start(
                message=self.msg_store.cannot_move_something_in_picking_type()
            )

        move_lines = self.search_move_line.search_move_lines(
            locations=location,
            match_user=True,
            picking_type=self.env[
                "stock.picking.type"
            ],  # disable filtering on picking types
        )
        move_lines = self._select_move_lines_first_location(move_lines)

        savepoint = self._actions_for("savepoint").new()
        unreserve = self._actions_for("stock.unreserve")

        unreserved_moves = self.env["stock.move"].browse()
        if self.work.menu.allow_unreserve_other_moves:
            message = unreserve.check_unreserve(location, move_lines)
            if message:
                return self._response_for_start(message=message)
            move_lines, unreserved_moves = unreserve.unreserve_moves(
                move_lines, self.picking_types
            )
        else:
            picking_types = move_lines.picking_id.picking_type_id
            if len(picking_types) > 1:
                return self._response_for_start(
                    message={
                        "message_type": "error",
                        "body": _("This location content can't be moved at once."),
                    }
                )
            if picking_types - self.picking_types:
                return self._response_for_start(
                    message=self.msg_store.cannot_move_something_in_picking_type()
                )

        if not move_lines:
            if not self.is_allow_move_create():
                savepoint.rollback()
                return self._response_for_start(
                    message=self.msg_store.location_empty(location)
                )
            new_moves = self._create_moves_from_location(location)
            if not new_moves:
                savepoint.rollback()
                return self._response_for_start(
                    message=self.msg_store.location_empty(location)
                )
            new_moves._action_confirm(merge=False)
            new_moves._action_assign()
            if not all([x.state == "assigned" for x in new_moves]):
                savepoint.rollback()
                return self._response_for_start(
                    message=self.msg_store.new_move_lines_not_assigned()
                )
            move_lines = new_moves.move_line_ids
            for line in move_lines:
                if not self.is_dest_location_valid(line.move_id, line.location_dest_id):
                    savepoint.rollback()
                    return self._response_for_start(
                        message=self.msg_store.location_content_unable_to_transfer(
                            location
                        )
                    )

        stock = self._actions_for("stock")
        if self.work.menu.ignore_no_putaway_available and stock.no_putaway_available(
            self.picking_types, move_lines
        ):
            # the putaway created a move line but no putaway was possible, so revert
            # to the initial state
            savepoint.rollback()
            return self._response_for_start(
                message=self.msg_store.no_putaway_destination_available()
            )

        stock.mark_move_line_as_picked(move_lines)

        unreserved_moves._action_assign()

        savepoint.release()

        return self._router_single_or_all_destination(move_lines.picking_id)

    def _find_transfer_move_lines_domain(self, location):
        return [
            ("location_id", "=", location.id),
            ("state", "in", ("assigned", "partially_available")),
            ("qty_done", ">", 0),
            # TODO check generated SQL
            ("picking_id.user_id", "=", self.env.uid),
        ]

    def _find_transfer_move_lines(self, location):
        """Find move lines currently being moved by the user"""
        lines = self.env["stock.move.line"].search(
            self._find_transfer_move_lines_domain(location)
        )
        return lines

    # hook used in module shopfloor_checkout_sync
    def _write_destination_on_lines(self, lines, location):
        lines.location_dest_id = location
        lines.package_level_id.picking_id.location_dest_id = location

    def _set_all_destination_lines_and_done(self, pickings, move_lines, dest_location):
        self._write_destination_on_lines(move_lines, dest_location)
        stock = self._actions_for("stock")
        stock.validate_moves(move_lines.move_id)

    def _lock_lines(self, lines):
        """Lock move lines"""
        self._actions_for("lock").for_update(lines)

    def set_destination_all(self, location_id, barcode, confirmation=None):
        """Scan destination location for all the moves of the location

        barcode is a stock.location for the destination

        Transitions:
        * scan_destination_all: invalid destination or could not set moves to done
        * start: moves are done
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_transfer_move_lines(location)
        pickings = move_lines.mapped("picking_id")
        if not pickings:
            # if we can't find the lines anymore, they likely have been done
            # by someone else
            return self._response_for_start(message=self.msg_store.already_done())
        scanned_location = self._actions_for("search").location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_scan_destination_all(
                pickings, message=self.msg_store.barcode_not_found()
            )

        if not self.is_dest_location_valid(move_lines.move_id, scanned_location):
            return self._response_for_scan_destination_all(
                pickings, message=self.msg_store.dest_location_not_allowed()
            )
        if confirmation != barcode and self.is_dest_location_to_confirm(
            move_lines.location_dest_id, scanned_location
        ):
            return self._response_for_scan_destination_all(
                pickings, confirmation_required=barcode
            )
        self._lock_lines(move_lines)

        self._set_all_destination_lines_and_done(pickings, move_lines, scanned_location)

        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(move_lines)
        return self._response_for_start(
            message=self.msg_store.location_content_transfer_complete(
                location, scanned_location
            ),
            popup=completion_info_popup,
        )

    def go_to_single(self, location_id):
        """Ask the first move line or package level

        If the user was brought to the screen allowing to move everything to
        the same location, but they want to move them to different locations,
        this method will return the first move line or package level.

        Transitions:
        * start: no remaining lines in the location
        * start_single: if any line or package level has a different destination
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_transfer_move_lines(location)
        if not move_lines:
            return self._response_for_start(
                message=self.msg_store.no_lines_to_process()
            )
        return self._response_for_start_single(move_lines.mapped("picking_id"))

    def scan_package(self, location_id, package_level_id, barcode):
        """Scan a package level to move

        It validates that the user scanned the correct package, lot or product.

        Transitions:
        * start: no remaining lines in the location
        * start_single: barcode not found, ...
        * scan_destination: the barcode matches
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(
                move_lines.mapped("picking_id"),
                message=self.msg_store.record_not_found(),
            )

        search = self._actions_for("search")
        package = search.package_from_scan(barcode)
        if package and package_level.package_id == package:
            return self._response_for_scan_destination(location, package_level)

        move_lines = self._find_transfer_move_lines(location)
        package_move_lines = package_level.move_line_ids
        other_move_lines = move_lines - package_move_lines

        product = search.product_from_scan(barcode)
        if not product:
            packaging = search.packaging_from_scan(barcode)
            product = packaging.product_id
        # Normally the user scan the barcode of the package. But if they scan the
        # product and we can be sure it's the correct package, it's tolerated.
        if product and product in package_move_lines.mapped("product_id"):
            if product in other_move_lines.mapped("product_id") or product.tracking in (
                "lot",
                "serial",
            ):
                # When the product exists in other move lines as raw products
                # or part of another package, we can't be sure they scanned
                # the correct package, so ask to scan the package.
                return self._response_for_start_single(
                    move_lines.mapped("picking_id"),
                    message={"message_type": "error", "body": _("Scan the package")},
                )
            else:
                return self._response_for_scan_destination(location, package_level)

        lot = search.lot_from_scan(barcode, products=package_move_lines.product_id)
        if lot and lot in package_move_lines.mapped("lot_id"):
            if lot in other_move_lines.mapped("lot_id"):
                return self._response_for_start_single(
                    move_lines.mapped("picking_id"),
                    message={"message_type": "error", "body": _("Scan the package")},
                )
            else:
                return self._response_for_scan_destination(location, package_level)

        # Nothing matches what is expected from the move line.
        for rec in (package, product, lot):
            if rec:
                return self._response_for_start_single(
                    move_lines.mapped("picking_id"),
                    message=self.msg_store.wrong_record(rec),
                )
        return self._response_for_start_single(
            move_lines.mapped("picking_id"), message=self.msg_store.barcode_not_found()
        )

    def scan_line(self, location_id, move_line_id, barcode):
        """Scan a move line to move

        It validates that the user scanned the correct package, lot or product.

        Transitions:
        * start: no remaining lines in the location
        * start_single: barcode not found, ...
        * scan_destination: the barcode matches
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(
                move_lines.mapped("picking_id"),
                message=self.msg_store.record_not_found(),
            )

        search = self._actions_for("search")

        package = search.package_from_scan(barcode)
        if package and move_line.package_id == package:
            # In case we have a source package but no package level because if
            # we have a package level, we would use "scan_package".
            return self._response_for_scan_destination(location, move_line)

        product = search.product_from_scan(barcode)
        if not product:
            packaging = search.packaging_from_scan(barcode)
            if packaging:
                product = packaging.product_id

        if product and product == move_line.product_id:
            if product.tracking in ("lot", "serial"):
                move_lines = self._find_transfer_move_lines(location)
                return self._response_for_start_single(
                    move_lines.mapped("picking_id"),
                    message=self.msg_store.scan_lot_on_product_tracked_by_lot(),
                )
            else:
                return self._response_for_scan_destination(location, move_line)

        lot = search.lot_from_scan(barcode, products=move_line.product_id)
        if lot and lot == move_line.lot_id:
            return self._response_for_scan_destination(location, move_line)

        # Nothing matches what is expected from the move line.
        move_lines = self._find_transfer_move_lines(location)
        for rec in (package, product, lot):
            if rec:
                return self._response_for_start_single(
                    move_lines.mapped("picking_id"),
                    message=self.msg_store.wrong_record(rec),
                )
        return self._response_for_start_single(
            move_lines.mapped("picking_id"), message=self.msg_store.barcode_not_found()
        )

    def set_destination_package(
        self, location_id, package_level_id, barcode, confirmation=None
    ):
        """Scan destination location for package level

        If the move has other move lines / package levels it has to be split
        so we can post only this part.

        After the destination is set, the move is set to done.

        Transitions:
        * scan_destination: invalid destination or could not
        * start_single: continue with the next package level / line
        * start: if there is no more package level / line to process
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(move_lines.mapped("picking_id"))
        search = self._actions_for("search")
        scanned_location = search.location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_scan_destination(
                location, package_level, message=self.msg_store.no_location_found()
            )
        package_moves = package_level.move_line_ids.move_id
        if not self.is_dest_location_valid(package_moves, scanned_location):
            return self._response_for_scan_destination(
                location,
                package_level,
                message=self.msg_store.dest_location_not_allowed(),
            )
        if confirmation != barcode and self.is_dest_location_to_confirm(
            package_level.location_dest_id, scanned_location
        ):
            return self._response_for_scan_destination(
                location, package_level, confirmation_required=barcode
            )
        package_move_lines = package_level.move_line_ids
        self._lock_lines(package_move_lines)
        stock = self._actions_for("stock")
        stock.put_package_level_in_move(package_level)
        self._write_destination_on_lines(package_level.move_line_ids, scanned_location)
        stock.validate_moves(package_moves)
        move_lines = self._find_transfer_move_lines(location)
        message = self.msg_store.location_content_transfer_item_complete(
            scanned_location
        )
        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(package_moves.move_line_ids)
        return self._response_for_start_single(
            move_lines.mapped("picking_id"),
            message=message,
            popup=completion_info_popup,
        )

    def set_destination_line(
        self, location_id, move_line_id, quantity, barcode, confirmation=None
    ):
        """Scan destination location for move line

        If the quantity < qty of the line, split the move and reserve it.
        If the move has other move lines / package levels it has to be split
        so we can post only this part.

        After the destination and quantity are set, the move is set to done.

        Transitions:
        * scan_destination: invalid destination or could not
        * start_single: continue with the next package level / line
        * start: if there is no more package level / line to process
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(move_lines.mapped("picking_id"))
        search = self._actions_for("search")
        scanned_location = search.location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_scan_destination(
                location, move_line, message=self.msg_store.no_location_found()
            )
        if not self.is_dest_location_valid(move_line.move_id, scanned_location):
            return self._response_for_scan_destination(
                location, move_line, message=self.msg_store.dest_location_not_allowed()
            )
        if confirmation != barcode and self.is_dest_location_to_confirm(
            move_line.location_dest_id, scanned_location
        ):
            return self._response_for_scan_destination(
                location, move_line, confirmation_required=barcode
            )

        self._lock_lines(move_line)

        move_line.qty_done = quantity
        self._write_destination_on_lines(move_line, scanned_location)

        stock = self._actions_for("stock")

        backorders = stock.validate_moves(move_line.move_id)
        if backorders:
            for move_line in backorders.mapped("move_line_ids"):
                move_line.qty_done = move_line.reserved_uom_qty
            backorders.user_id = self.env.user
            # process first backorder of current line
            move_lines = backorders.move_line_ids
        else:
            move_lines = self._find_transfer_move_lines(move_line.location_id)
        message = self.msg_store.location_content_transfer_item_complete(
            scanned_location
        )
        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(move_line)
        return self._response_for_start_single(
            move_lines.mapped("picking_id"),
            message=message,
            popup=completion_info_popup,
        )

    def postpone_package(self, location_id, package_level_id):
        """Mark a package level as postponed and return the next level/line

        Transitions:
        * start_single: continue with the next package level / line
        """
        location = self.env["stock.location"].browse(location_id)
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_lines = self._find_transfer_move_lines(location)
        if package_level.exists():
            pickings = move_lines.mapped("picking_id")
            sorter = self._actions_for("location_content_transfer.sorter")
            sorter.feed_pickings(pickings)
            package_levels = sorter.package_levels()
            package_level.shopfloor_postpone(move_lines, package_levels)
        return self._response_for_start_single(move_lines.mapped("picking_id"))

    def postpone_line(self, location_id, move_line_id):
        """Mark a move line as postponed and return the next level/line

        Transitions:
        * start_single: continue with the next package level / line
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        move_lines = self._find_transfer_move_lines(location)
        if move_line.exists():
            pickings = move_lines.mapped("picking_id")
            sorter = self._actions_for("location_content_transfer.sorter")
            sorter.feed_pickings(pickings)
            package_levels = sorter.package_levels()
            move_line.shopfloor_postpone(move_lines, package_levels)
        return self._response_for_start_single(move_lines.mapped("picking_id"))

    def stock_out_package(self, location_id, package_level_id):
        """Declare a stock out on a package level

        It first ensures the stock.move only has this package level. If not, it
        splits the move to have no side-effect on the other package levels/move
        lines.

        If the move has been created by the shopfloor user it will be canceled
        otherwise it is unreserved.
        Then create an inventory at 0 in the move's source location, create a
        second draft inventory (if none exists) to check later.

        Transitions:
        * start: no more content to move
        * start_single: continue with the next package level / line
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(move_lines.mapped("picking_id"))
        inventory = self._actions_for("inventory")
        package_move_lines = package_level.move_line_ids
        package_moves = package_move_lines.mapped("move_id")
        package = package_level.package_id
        for package_move in package_moves:
            # Check if there is no other lines linked to the move others than
            # the lines related to the package itself. In such case we have to
            # split the move to process only the lines related to the package.
            package_move.split_other_move_lines(package_move_lines)
            lot = package_move.move_line_ids.lot_id
            # We need to set qty_done at 0 because otherwise
            # the move_line will not be deleted
            package_move.move_line_ids.write({"qty_done": 0})
            package = package_level.package_id
            if (
                self.is_allow_move_create()
                and self.env.user == package_move.picking_id.create_uid
            ):
                # Owned by the user deleting the move
                package_move._action_cancel()
            else:
                # Not owned only unreserved
                package_move._do_unreserve()
                package_move._recompute_state()
            # Create an inventory at 0 in the move's source location
            inventory.create_stock_issue(package_move, location, package, lot)
            # Create a draft inventory to control stock
            inventory.create_control_stock(
                location, package_move.product_id, package, lot
            )
        # remove the package level (this is what does the `picking.do_unreserve()`
        # method, but here we want to unreserve+unlink this package alone)
        move_lines = self._find_transfer_move_lines(location)
        return self._response_for_start_single(move_lines.mapped("picking_id"))

    def stock_out_line(self, location_id, move_line_id):
        """Declare a stock out on a move line

        It first ensures the stock.move only has this move line. If not, it
        splits the move to have no side-effect on the other package levels/move
        lines.

        If the move has been created by the shopfloor user it will be canceled
        otherwise it will be unreserved.
        Then an inventory is created at 0 in the move's source location,
        create a second draft inventory (if none exists) to check later.

        Transitions:
        * start: no more content to move
        * start_single: continue with the next package level / line
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(move_lines.mapped("picking_id"))
        inventory = self._actions_for("inventory")
        move_line.move_id.split_other_move_lines(move_line)
        move_line_src_location = move_line.location_id
        move = move_line.move_id
        package = move_line.package_id
        lot = move_line.lot_id
        # We need to set qty_done at 0 because otherwise
        # the move_line will not be deleted
        move_line.qty_done = 0
        if self.is_allow_move_create() and self.env.user == move.picking_id.create_uid:
            # Owned by the user deleting the move
            move._action_cancel()
        else:
            # Not owned unreserve
            move._do_unreserve()
            move._recompute_state()
        # Create an inventory at 0 in the move's source location
        inventory.create_stock_issue(move, move_line_src_location, package, lot)
        # Create a draft inventory to control stock
        inventory.create_control_stock(
            move_line_src_location, move.product_id, package, lot
        )
        move_lines = self._find_transfer_move_lines(location)
        return self._response_for_start_single(move_lines.mapped("picking_id"))

    def dismiss_package_level(self, location_id, package_level_id):
        """Dismiss the package level.

        The result package of the related move lines is unset, then the package
        level itself is removed from the picking. This allows to move parts
        of the package to different locations.

        The user is then redirected to process the next line of the related picking.

        Transitions:
        * start_single: continue with the next line
        """
        location = self.env["stock.location"].browse(location_id)
        if not location.exists():
            return self._response_for_start(message=self.msg_store.record_not_found())
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            move_lines = self._find_transfer_move_lines(location)
            return self._response_for_start_single(
                move_lines.mapped("picking_id"),
                message=self.msg_store.record_not_found(),
            )
        move_lines = package_level.move_line_ids
        package_level.explode_package()
        move_lines.write(
            {
                # ensure all the lines in the package are the next ones to be processed
                "shopfloor_priority": 1,
            }
        )
        return self._response_for_start_single(
            move_lines.mapped("picking_id"), message=self.msg_store.package_open()
        )


class ShopfloorLocationContentTransferValidator(Component):
    """Validators for the Location Content Transfer endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.location.content.transfer.validator"
    _usage = "location_content_transfer.validator"

    def start_or_recover(self):
        return {}

    def get_work(self):
        return {}

    def cancel_work(self):
        return {"location_id": {"required": True, "type": "integer"}}

    def scan_location(self):
        return {"barcode": {"required": True, "type": "string"}}

    def set_destination_all(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "string", "nullable": True, "required": False},
        }

    def go_to_single(self):
        return {"location_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_destination_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "string", "nullable": True, "required": False},
        }

    def set_destination_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "string", "nullable": True, "required": False},
        }

    def postpone_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def postpone_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def stock_out_package(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def stock_out_line(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def dismiss_package_level(self):
        return {
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorLocationContentTransferValidatorResponse(Component):
    """Validators for the Location Content Transfer endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.location.content.transfer.validator.response"
    _usage = "location_content_transfer.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "scan_location": {},
            "get_work": {},
            "scan_destination_all": self._schema_all,
            "start_single": self._schema_single,
            "scan_destination": self._schema_single,
        }

    @property
    def _schema_all(self):
        package_level_schema = self.schemas.package_level()
        move_line_schema = self.schemas.move_line()
        return {
            "location": self.schemas._schema_dict_of(self.schemas.location()),
            # we'll display all the packages and move lines *without package
            # levels*
            "package_levels": self.schemas._schema_list_of(package_level_schema),
            "move_lines": self.schemas._schema_list_of(move_line_schema),
            "confirmation_required": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
        }

    @property
    def _schema_single(self):
        schema_package_level = self.schemas.package_level()
        schema_move_line = self.schemas.move_line()
        return {
            # we'll have one or the other...
            "package_level": self.schemas._schema_dict_of(schema_package_level),
            "move_line": self.schemas._schema_dict_of(schema_move_line),
            "confirmation_required": {
                "type": "string",
                "nullable": True,
                "required": False,
            },
        }

    def start_or_recover(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "scan_destination_all",
                "start_single",
                "get_work",
            }
        )

    def scan_location(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "get_work",
                "scan_destination_all",
                "start_single",
            }
        )

    def set_destination_all(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "scan_destination_all"}
        )

    def go_to_single(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )

    def scan_package(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "get_work",
                "start_single",
                "scan_destination",
            }
        )

    def scan_line(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "get_work",
                "start_single",
                "scan_destination",
            }
        )

    def set_destination_package(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "get_work",
                "start_single",
                "scan_destination",
            }
        )

    def set_destination_line(self):
        return self._response_schema(
            next_states={
                "scan_location",
                "get_work",
                "start_single",
                "scan_destination",
            }
        )

    def postpone_package(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )

    def postpone_line(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )

    def stock_out_package(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )

    def stock_out_line(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )

    def dismiss_package_level(self):
        return self._response_schema(
            next_states={"scan_location", "get_work", "start_single"}
        )
