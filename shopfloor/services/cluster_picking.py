from odoo import _, fields

from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float


class ClusterPicking(Component):
    """
    Methods for the Cluster Picking Process

    The goal of this process is to do the pickings for a Picking Batch, for
    several customers at once.
    The process assumes that picking batch records already exist.

    At first, a user gets automatically a batch to work on (assigned to them),
    or can select one from a list.

    The process has 2 main phases, which can be done one after the other or a
    bit of both. The first one is picking goods and put them in a roller-cage.

    First phase, picking:

    * Pick a good (move line) from a source location, scan it to confirm it's
      the expected one
    * Scan the label of a Bin (package) in a roller-cage, put the good inside
      (physically). Once the first move line of a picking has been scanned, the
      screen will show the same destination package for all the other lines of
      the picking to help the user grouping goods together, and will prevent
      lines from other pickings to be put in the same destination package.
    * If odoo thinks a source location is empty after picking the goods, a
      "zero check" is done: it asks the user to confirm if it is empty or not
    * Repeat until the end of the batch or the roller-cage is full (there is
      button to declare this)

    Second phase, unload to destination:

    * If all the goods (move lines) in the roller-cage go to the same destination,
      a screen asking a single barcode for the destination is shown
    * Otherwise, the user has to scan one destination per Bin (destination
      package of the moves).
    * If all the goods are supposed to go to the same destination but user doesn't
      want or can't, a "split" allows to reach the screen to scan one destination
      per Bin.
    * When everything has a destination set and the batch is not finished yet,
      the user goes to the first phase of pickings again for the rest.

    Inside the main workflow, some actions are accessible from the client:

    * Change a lot or pack: if the expected lot is at the very bottom of the
      location or a stock error forces a user to change lot or pack, user can
      do it during the picking.
    * Skip a line: during picking, for instance because a line is not accessible
      easily, it can be postponed, note that skipped lines have to be done, they
      are only moved to the end of the queue.
    * Declare stock out: if a good is in fact not in stock or only partially. Note
      the move lines will become unavailable or partially unavailable and will
      generate a back-order.
    * Full bin: declaring a full bin allows to move directly to the first phase
      (picking) to the second one (unload). The process will go
      back to the first phase if some lines remain in the queue of lines to pick.

    Flow Diagram: https://www.draw.io/#G1qRenBcezk50ggIazDuu2qOfkTsoIAxXP
    """

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.cluster.picking"
    _usage = "cluster_picking"
    _description = __doc__

    def find_batch(self):
        """Find a picking batch to work on and start it

        Usually the starting point of the process.

        Business rules to find a batch, try in order:

        a. Find a batch in progress assigned to the current user
        b. Find a draft batch assigned to the current user:
          1. set it to 'in progress'
        c. Find an unassigned draft batch:
          1. assign batch to the current user
          2. set it to 'in progress'

        Transitions:
        * confirm_start: when it could find a batch
        * start: when no batch is available
        """
        batch_service = self.component(usage="picking_batch")
        batches = batch_service._search()
        selected = self._select_a_picking_batch(batches)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response_for_no_batch_found()

    def list_batch(self):
        """List picking batch on which user can work

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        batch_service = self.component(usage="picking_batch")
        batches = batch_service.search()["data"]
        return self._response(next_state="manual_selection", data=batches)

    # TODO this may be used in other scenarios? if so, extract
    def _select_a_picking_batch(self, batches):
        # look for in progress + assigned to self first
        candidates = batches.filtered(
            lambda batch: batch.state == "in_progress"
            and batch.user_id == self.env.user
        )
        if candidates:
            return candidates[0]
        # then look for draft assigned to self
        candidates = batches.filtered(lambda batch: batch.user_id == self.env.user)
        if candidates:
            batch = candidates[0]
            batch.write({"state": "in_progress"})
            return batch
        # finally take any batch that search could return
        if batches:
            batch = batches[0]
            batch.write({"user_id": self.env.uid, "state": "in_progress"})
            return batch
        return self.env["stock.picking.batch"]

    def _response_for_no_batch_found(self):
        return self._response(
            next_state="start",
            message={
                "message_type": "info",
                "message": _("No more work to do, please create a new batch transfer"),
            },
        )

    def _response_for_confirm_start(self, batch):
        pickings = []
        for picking in batch.picking_ids:
            # TODO: is this correct?
            p_weight = sum(picking.mapped("move_line_ids.product_id.weight"))
            p_values = {
                "id": picking.id,
                "name": picking.name,
                "partner": None,
                "move_line_count": len(picking.move_line_ids),
                "weight": p_weight,
                "origin": picking.origin or "",
            }
            if picking.partner_id:
                p_values["partner"] = {
                    "id": picking.partner_id.id,
                    "name": picking.partner_id.name,
                }
            pickings.append(p_values)
        return self._response(
            next_state="confirm_start",
            data={"id": batch.id, "name": batch.name, "pickings": pickings},
        )

    def _response_for_batch_cannot_be_selected(self):
        return self._response(
            base_response=self.list_batch(),
            message={
                "message_type": "warning",
                "message": _("This batch cannot be selected."),
            },
        )

    def select(self, picking_batch_id):
        """Manually select a picking batch

        The client application can use the service /picking_batch/search
        to get the list of candidate batches. Then, it starts to work on
        the selected batch by calling this.

        Note: it should be able to work only on batches which are in draft or
        (in progress and assigned to the current user), the search method that
        lists batches filter them, but it has to be checked again here in case
        of race condition.

        Transitions:
        * manual_selection: a selected batch cannot be used (assigned to someone else
          concurrently for instance)
        * confirm_start: after the batch has been assigned to the user
        """
        batch_service = self.component(usage="picking_batch")
        batch = batch_service._search(batch_ids=[picking_batch_id])
        selected = self._select_a_picking_batch(batch)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response_for_batch_cannot_be_selected()

    def confirm_start(self, picking_batch_id):
        """User confirms they start a batch

        Should have no effect in odoo besides logging and routing the user to
        the next action. The next action is "start_line" with data about the
        line to pick.

        Transitions:
        * start_line: when the batch has at least one line without destination
          package
        * start: if the condition above is wrong (rare case of race condition...)
        """
        picking_batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not picking_batch.exists():
            return self._response_batch_does_not_exist()

        next_line = self._next_line_for_pick(picking_batch)
        if not next_line:
            # TODO
            return self._response(
                next_state="start",
                message={
                    "message_type": "error",
                    "message": "No lines remaining. "
                    "Should go to 'Prepare unload' but is not implemented yet",
                },
            )

        return self._response(
            next_state="start_line", data=self._data_move_line(next_line)
        )

    def _lines_for_picking_batch(self, picking_batch, filter_func=lambda x: x):
        lines = picking_batch.mapped("picking_ids.move_line_ids").filtered(filter_func)
        # TODO we probably don't care about the postponed order in the 'set
        # destination location' step, reset it on 'scan_destination_pack'?
        # TODO test line sorting and all these methods to retrieve lines

        # Sort line by source location,
        # so that the picker start w/ products in the same location.
        # Postponed lines must come always
        # after ALL the other lines in the batch are processed.
        return lines.sorted(key=lambda x: (x.location_id, x.shopfloor_postponed))

    def _lines_to_pick(self, picking_batch):
        return self._lines_for_picking_batch(
            picking_batch,
            filter_func=lambda l: (
                l.state == "assigned"
                # On 'StockPicking.action_assign()', result_package_id is set to
                # the same package as 'package_id'. Here, we need to exclude lines
                # that were already put into a bin, i.e. the destination package
                # is different.
                and (not l.result_package_id or l.result_package_id == l.package_id)
            ),
        )

    def _last_picked_line(self, picking):
        """Get the last line packed for this picking."""
        return fields.first(
            picking.move_line_ids.filtered(
                lambda l: l.qty_done > 0 and l.result_package_id
            )
        )

    def _next_line_for_pick(self, picking_batch):
        remaining_lines = self._lines_to_pick(picking_batch)
        return fields.first(remaining_lines)

    def _response_batch_does_not_exist(self):
        message = self.actions_for("message")
        return self._response(next_state="start", message=message.record_not_found())

    def _data_for_next_move_line(self, picking_batch):
        remaining_lines = self._lines_to_pick(picking_batch)
        return self._data_move_line(remaining_lines[0])

    def _data_move_line(self, line):
        picking = line.picking_id
        batch = picking.batch_id
        product = line.product_id
        lot = line.lot_id
        package = line.package_id
        data = {
            # TODO have common methods to return general info
            # for each model
            "id": line.id,
            "quantity": line.product_uom_qty,
            "postponed": line.shopfloor_postponed,
            "picking": {
                "id": picking.id,
                "name": picking.name,
                "origin": picking.origin or "",
                "note": picking.note or "",
                "partner": None,
            },
            "batch": {"id": batch.id, "name": batch.name},
            "product": {
                "id": product.id,
                "name": product.name,
                "display_name": product.display_name,
                "default_code": product.default_code or "",
                "qty_available": product.qty_available,
            },
            "lot": {"id": lot.id, "name": lot.name, "ref": lot.ref or ""}
            if lot
            else None,
            "location_src": {"id": line.location_id.id, "name": line.location_id.name},
            "location_dst": {
                "id": line.location_dest_id.id,
                "name": line.location_dest_id.name,
            },
            "pack": {"id": package.id, "name": package.name} if package else None,
        }
        if picking.partner_id:
            # TODO retrieve info always in the same way
            # maybe using base_jsonify
            data["picking"]["partner"] = {
                "id": picking.partner_id.id,
                "name": picking.partner_id.name,
            }
        return data

    def unassign(self, picking_batch_id):
        """Unassign and reset to draft a started picking batch

        Transitions:
        * "start" to work on a new batch
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if batch.exists():
            batch.write({"state": "draft", "user_id": False})
        return self._response(next_state="start")

    def scan_line(self, move_line_id, barcode):
        """Scan a location, a pack, a product or a lots

        There is no side-effect, it is only to check that the operator takes
        the expected pack or product.

        User can scan a location if there is only pack inside. Otherwise, they
        have to precise what they want by scanning one of:

        * pack
        * product
        * lot

        The result must be unambigous. For instance if we scan a product but the
        product is tracked by lot, scanning the lot has to be required.

        Transitions:
        * start_line: with an appropriate message when user has
          to scan for the same line again
        * start_line: with the next line if the line was added to a
          pack meanwhile (race condition).
        * scan_destination: if the barcode matches.
        """
        message = self.actions_for("message")
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            # TODO go to next line? (but then handle if it's the last one)
            return self._response(next_state="start")
        # TODO check again the state of the move line, if already processed
        # move to the next state or next line
        if move_line.package_id.name == barcode:
            return self._response_for_scan_line_ok(move_line)
        elif move_line.product_id.barcode == barcode:
            if move_line.product_id.tracking in ("lot", "serial"):
                return self._response_for_scan_line_product_need_lot(move_line)
            return self._response_for_scan_line_ok(move_line)
        elif move_line.lot_id.name == barcode:
            return self._response_for_scan_line_ok(move_line)
        elif move_line.location_id.barcode == barcode:
            # When a user scan a location, we accept only when we knows that
            # they scanned the good thing, so if in the location we have
            # several lots (on a package or a product), several packages,
            # several products or a mix of several products and packages, we
            # ask to scan a more precise barcode.
            location = move_line.location_id
            packages = set()
            products = set()
            lots = set()
            for quant in location.quant_ids:
                if quant.quantity <= 0:
                    continue
                if quant.package_id:
                    packages.add(quant.package_id)
                else:
                    products.add(quant.product_id)
                if quant.lot_id:
                    lots.add(quant.lot_id)

            if len(lots) > 1:
                return self._response_for_scan_line_several_lots_in_loc(move_line)
            if len(packages | products) > 1:
                if move_line.package_id:
                    return self._response_for_scan_line_several_packages_in_loc(
                        move_line
                    )
                else:
                    return self._response_for_scan_line_several_products_in_loc(
                        move_line
                    )

            return self._response_for_scan_line_ok(move_line)

        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message.barcode_not_found(),
        )

    def _response_for_scan_line_several_lots_in_loc(self, move_line):
        message = self.actions_for("message")
        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message.several_lots_in_location(move_line.location_id),
        )

    def _response_for_scan_line_several_products_in_loc(self, move_line):
        message = self.actions_for("message")
        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message.several_products_in_location(move_line.location_id),
        )

    def _response_for_scan_line_several_packages_in_loc(self, move_line):
        message = self.actions_for("message")
        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message.several_packs_in_location(move_line.location_id),
        )

    def _response_for_scan_line_product_need_lot(self, move_line):
        message = self.actions_for("message")
        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message.scan_lot_on_product_tracked_by_lot(),
        )

    def _response_for_scan_line_ok(self, move_line):
        data = self._data_move_line(move_line)
        last_picked_line = self._last_picked_line(move_line.picking_id)
        if last_picked_line:
            # suggest pack to be used for the next line
            data["destination_pack"] = {
                "id": last_picked_line.result_package_id.id,
                "name": last_picked_line.result_package_id.name,
            }
        return self._response(next_state="scan_destination", data=data)

    def scan_destination_pack(self, move_line_id, barcode, quantity):
        """Scan the destination package (bin) for a move line

        If the quantity picked (passed to the endpoint) is < expected quantity,
        it splits the move line.
        It changes the destination package of the move line and set the "qty done".
        It prevents to put a move line of a picking in a destination package
        used for another picking.

        Transitions:
        * zero_check: if the quantity of product moved is 0 in the
        source location after the move (beware: at this point the product we put in
        a bin is still considered to be in the source location, so we have to compute
        the source location's quantity - qty_done).
        * unload_all: when all lines have a destination package and they all
        have the same destination.
        * unload_single: when all lines have a destination package and they all
        have the same destination.
        * start_line: to pick the next line if any.
        """
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            # TODO go to next line? (but then handle if it's the last one)
            return self._response(next_state="start")
        # TODO if another line of the picking has a destination package, handle
        # it (note: should be added to the 'single line' schema /data as well,
        # maybe use a computed field).

        # TODO handle partial pick
        if quantity > move_line.product_uom_qty:
            # TODO (+ use float_tools)
            return self._response()
        # TODO handle destination bin not empty
        search = self.actions_for("search")
        bin_package = search.package_from_scan(barcode)
        if not bin_package:
            # TODO
            return self._response()
        move_line.write({"qty_done": quantity, "result_package_id": bin_package.id})
        # TODO zero check
        # TODO handle next line and no next line (in a shared way with other
        # endpoints)
        batch = move_line.picking_id.batch_id
        next_line = self._next_line_for_pick(batch)
        if not next_line:
            return self.prepare_unload(batch.id)
        return self._response(
            next_state="start_line",
            data=self._data_move_line(next_line),
            message={
                "message_type": "success",
                # TODO different message for products/packs?
                "message": _("{} {} put in {}").format(
                    move_line.qty_done,
                    move_line.product_id.display_name,
                    bin_package.name,
                ),
            },
        )

    def _are_all_dest_location_same(self, batch):
        lines_to_unload = self._lines_to_unload(batch)
        return len(lines_to_unload.mapped("location_dest_id")) == 1

    def prepare_unload(self, picking_batch_id):
        """Initiate the unloading phase of the process

        If the destination of all the move lines still to unload is the same,
        it sets the flag ``cluster_picking_unload_all`` to True on
        ``stock.batch.picking``.
        Everytime this method is called, it resets the flag according to the
        condition above.

        Transitions:
        * unload_all: when ``cluster_picking_unload_all`` is True
        * unload_single: when ``cluster_picking_unload_all`` is False
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if self._are_all_dest_location_same(batch):
            batch.cluster_picking_unload_all = True
            return self._response_for_unload_all(batch)
        else:
            # the lines have different destinations
            batch.cluster_picking_unload_all = False
            return self._response_for_unload_single(batch)

    def _data_for_unload_all(self, batch):
        lines = self._lines_to_unload(batch)
        # all the lines destinations are the same here, it looks
        # only for the first one
        first_line = fields.first(lines)
        return {
            "id": batch.id,
            "name": batch.name,
            "location_dst": {
                "id": first_line.location_dest_id.id,
                "name": first_line.location_dest_id.name,
            },
        }

    def _data_for_unload_single(self, batch, package):
        line = fields.first(
            package.dest_move_line_ids.filtered(self._filter_for_unload)
        )
        return {
            # TODO disambiguate "id" everywhere? (id -> picking_batch_id)
            "id": batch.id,
            "name": batch.name,
            "package": {"id": package.id, "name": package.name},
            "location_dst": {
                "id": line.location_dest_id.id,
                "name": line.location_dest_id.name,
            },
        }

    def _response_for_unload_all(self, batch, message=None):
        return self._response(
            next_state="unload_all",
            data=self._data_for_unload_all(batch),
            message=message,
        )

    def _response_for_unload_all_need_confirm(self, batch, message=None):
        return self._response(
            next_state="confirm_unload_all",
            data=self._data_for_unload_all(batch),
            message=message,
        )

    def _filter_for_unload(self, line):
        return (
            line.qty_done > 0 and line.result_package_id and not line.shopfloor_unloaded
        )

    def _lines_to_unload(self, batch):
        return self._lines_for_picking_batch(batch, filter_func=self._filter_for_unload)

    def _bin_packages_to_unload(self, batch):
        lines = self._lines_to_unload(batch)
        packages = lines.mapped("result_package_id")
        return packages

    def _next_bin_package_for_unload_single(self, batch):
        packages = self._bin_packages_to_unload(batch)
        return fields.first(packages)

    def _response_for_unload_single(self, batch):
        next_package = self._next_bin_package_for_unload_single(batch)
        if not next_package:
            # TODO ensure batch is 'done' and go to start?
            return self._response()
        return self._response(
            next_state="unload_single",
            data=self._data_for_unload_single(batch, next_package),
        )

    def is_zero(self, move_line_id, zero):
        """Confirm or not if the source location of a move has zero qty

        If the user confirms there is zero quantity, it means the stock was
        correct and there is nothing to do. If the user says "no", a draft
        empty inventory is created for the product (with lot if tracked).

        Transitions:
        * start_line: if the batch has lines without destination package (bin)
        * unload_all: if all lines have a destination package and same
          destination
        * unload_single: if all lines have a destination package and different
          destination
        """
        return self._response()

    def skip_line(self, move_line_id):
        """Skip a line. The line will be processed at the end.

        It adds a flag on the move line, when the next line to pick
        is searched, lines with such flag at moved to the end.

        A skipped line *must* be picked.

        Transitions:
        * start_line: with data for the next line (or itself if it's the last one,
        in such case, a helpful message is returned)
        """
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            # TODO go to next line? (but then handle if it's the last one)
            return self._response(next_state="start")
        # flag as postponed
        move_line.shopfloor_postponed = True
        return self._response_for_skip_line(move_line)

    def _response_for_skip_line(self, move_line):
        next_line = self._next_line_for_pick(move_line.picking_id.batch_id)
        if not next_line:
            # TODO ensure batch is 'done' and go to start?
            return self._response(
                next_state="start",
                message={
                    "message_type": "error",
                    "message": "no lines remaining, not implemented",
                },
            )
        return self._response(
            next_state="start_line", data=self._data_move_line(next_line)
        )

    def stock_issue(self, move_line_id):
        """Declare a stock issue for a line

        After errors in the stock, the user cannot take all the products
        because there is physically not enough goods. The move line is
        unassigned, and an inventory is created to reduce the quantity in the
        source location to prevent future errors until a correction. Beware:
        the quantity already reserved by other lines should remain reserved so
        the inventory's quantity must be set to the quantity of lines reserved
        by other move lines (but not the current one).

        A second inventory is created in draft to have someone do an inventory.

        Transitions:
        * start_line: when the batch still contains lines without destination
          package
        * unload_all: if all lines have a destination package and same
          destination
        * unload_single: if all lines have a destination package and different
          destination
        * start: all lines are done/confirmed (because all lines were unloaded
          and the last line has a stock issue). In this case, this method *has*
          to handle the closing of the batch to create backorders. TODO find a
          generic way to share actions happening on transitions such as "close
          the batch"
        """
        return self._response()

    def change_pack_lot(self, move_line_id, barcode):
        """Change the expected pack or the lot for a line

        If the expected lot is at the very bottom of the location or a stock
        error forces a user to change lot or pack, user can change the pack or
        lot of the current line.

        The change occurs when the pack/product/lot is normally scanned and
        goes directly to the scan of the destination package (bin) since we do
        not need to check it.

        If the pack or lot was not supposed to be in the source location,
        a draft inventory is created to have this checked.

        Transitions:
        * scan_destination: the pack or the lot could be changed
        * start_line: any error occurred during the change
        """
        return self._response()

    def set_destination_all(self, picking_batch_id, barcode, confirmation=False):
        """Set the destination for all the lines of the batch with a dest. package

        This method must be used only if all the move lines which have a destination
        package and qty done have the same destination location.

        A scanned location outside of the source location of the operation type is
        invalid.

        Transitions:
        * start_line: the batch still have move lines without destination package
        * unload_all: invalid destination, have to scan a good one
        * confirm_unload_all: the scanned location is not the expected one (but
          still a valid one)
        * start: batch is totally done. In this case, this method *has*
          to handle the closing of the batch to create backorders. TODO find a
          generic way to share actions happening on transitions such as "close
          the batch"
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()

        message = self.actions_for("message")

        # In case /set_destination_all was called and the destinations were
        # in fact no the same... restart the unloading step over
        if not self._are_all_dest_location_same(batch):
            return self.prepare_unload(batch.id)

        lines = self._lines_to_unload(batch)
        if not lines:
            # TODO a bit unexpected here but deal with it
            return self._response()

        first_line = fields.first(lines)
        picking_type = fields.first(batch.picking_ids).picking_type_id
        scanned_location = self.actions_for("search").location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_unload_all(
                batch, message=message.no_location_found()
            )
        if not scanned_location.is_sublocation_of(
            picking_type.default_location_dest_id
        ):
            return self._response_for_unload_all(
                batch, message=message.dest_location_not_allowed()
            )

        if not scanned_location.is_sublocation_of(first_line.location_dest_id):
            if not confirmation:
                return self._response_for_unload_all_need_confirm(batch)

        lines.write(
            {"shopfloor_unloaded": True, "location_dest_id": scanned_location.id}
        )
        for line in lines:
            # We set the picking to done only when the last line is
            # unloaded to avoid backorders.
            picking = line.picking_id
            if picking.state == "done":
                continue
            picking_lines = picking.mapped("move_line_ids")
            if all(l.shopfloor_unloaded for l in picking_lines):
                picking.action_done()

        if all(picking.state == "done" for picking in batch.picking_ids):
            # do not use the 'done()' method because it does many things we
            # don't care about
            batch.state = "done"
            return self._response_batch_complete()

        next_line = self._next_line_for_pick(batch)
        if next_line:
            return self._response(
                next_state="start_line", data=self._data_move_line(next_line)
            )
        else:
            # TODO add tests for this (for instance a picking is not 'done'
            # because a move was unassigned, we want to validate the batch to
            # produce backorders)
            batch.mapped("picking_ids").action_done()
            batch.state = "done"
            return self._response_batch_complete()

    def _response_batch_complete(self):
        return self._response(
            next_state="start",
            message={
                "message_type": "success",
                "message": _("Batch Transfer complete"),
            },
        )

    def unload_split(self, picking_batch_id):
        """Indicates that now the batch must be treated line per line

        Even if the move lines to unload all have the same destination.

        It sets the flag ``stock_picking_batch.cluster_picking_unload_all`` to
        False.

        Note: if we go back to the first phase of picking and start a new
        phase of unloading, the flag is reevaluated to the initial condition.

        Transitions:
        * unload_single: always goes here since we now want to unload line per line
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()

        batch.cluster_picking_unload_all = False

        return self._response_for_unload_single(batch)

    def unload_router(self, picking_batch_id):
        """Called after the info screen, route to the next state

        No side effect in Odoo.

        Transitions:
        * unload_single: if the batch still has packs to unload
        * start_line: if the batch still has lines to pick
        * start: if the batch is done. In this case, this method *has*
          to handle the closing of the batch to create backorders. TODO find a
          generic way to share actions happening on transitions such as "close
          the batch"
        """
        return self._response()

    def unload_scan_pack(self, picking_batch_id, package_id, barcode):
        """Check that the operator scans the correct package (bin) on unload

        If the scanned barcode is not the one of the Bin (package), ask to scan
        again.

        Transitions:
        * unload_single: if the barcode does not match
        * unload_set_destination: barcode is correct
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        package = self.env["stock.quant.package"].browse(package_id)
        if not package.exists():
            # TODO: next package? if no next package, close and go to start?
            return self._response()
        if package.name != barcode:
            return self._response(
                next_state="unload_single",
                data=self._data_for_unload_single(batch, package),
                message={"message_type": "error", "message": _("Wrong bin")},
            )
        return self._response(
            next_state="unload_set_destination",
            data=self._data_for_unload_single(batch, package),
        )

    def unload_scan_destination(
        self, picking_batch_id, package_id, barcode, confirmation=False
    ):
        """Scan the final destination for all the move lines moved with the Bin

        It updates all the assigned move lines with the package to the
        destination.

        TODO not sure: We have to call action_done on the picking *only when we
        have scanned all the packages* of the picking, so maybe we have to
        keep track of this with a new flag on move lines?

        Transitions:
        * unload_single: invalid scanned location or error
        * unload_single: line is processed and the next bin can be unloaded
        * confirm_unload_set_destination: the destination is valid but not the
          expected, ask a confirmation. This state has to call again the
          endpoint with confirmation=True
        * show_completion_info: the completion info of the picking is
          "next_picking_ready", it will show an info box to the user, the js
          client should then call /unload_router to know the next state
        * start_line: if the batch still has lines to pick
        * start: if the batch is done. In this case, this method *has*
          to handle the closing of the batch to create backorders. TODO find a
          generic way to share actions happening on transitions such as "close
          the batch"

        """
        return self._response()


class ShopfloorClusterPickingValidator(Component):
    """Validators for the Cluster Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.cluster_picking.validator"
    _usage = "cluster_picking.validator"

    def find_batch(self):
        return {}

    def list_batch(self):
        return {}

    def select(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def confirm_start(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def unassign(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def scan_line(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_destination_pack(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "quantity": {"coerce": to_float, "required": True, "type": "float"},
        }

    def prepare_unload(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def is_zero(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "zero": {"coerce": to_bool, "required": True, "type": "boolean"},
        }

    def skip_line(self):
        return {"move_line_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def stock_issue(self):
        return {"move_line_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def change_pack_lot(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def set_destination_all(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def unload_split(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def unload_router(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def unload_scan_pack(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def unload_scan_destination(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "package_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class ShopfloorClusterPickingValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.cluster_picking.validator.response"
    _usage = "cluster_picking.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "confirm_start": self._schema_for_batch_details,
            "start_line": self._schema_for_single_line_details,
            "start": {},
            "manual_selection": self._schema_for_batch_selection,
            "scan_destination": self._schema_for_single_line_details,
            "zero_check": self._schema_for_zero_check,
            "unload_all": self._schema_for_unload_all,
            "confirm_unload_all": self._schema_for_unload_all,
            "unload_single": self._schema_for_unload_single,
            "unload_set_destination": self._schema_for_unload_single,
            "confirm_unload_set_destination": self._schema_for_unload_single,
            "show_completion_info": self._schema_for_completion_info,
        }

    def find_batch(self):
        return self._response_schema(next_states=["confirm_start", "start"])

    def list_batch(self):
        return self._response_schema(next_states=["manual_selection"])

    def select(self):
        return self._response_schema(next_states=["manual_selection", "confirm_start"])

    def confirm_start(self):
        return self._response_schema(
            next_states=[
                "start_line",
                # "start" should be pretty rare, only if the batch has been
                # canceled, deleted meanwhile...
                # TODO every state could bring back to 'start' in case of
                # unrecoverable error, maybe we should add an attribute
                # `_start_state = "start"` and implicitly add it in states
                "start",
            ]
        )

    def unassign(self):
        return self._response_schema(next_states=["start"])

    def scan_line(self):
        return self._response_schema(next_states=["start_line", "scan_destination"])

    def scan_destination_pack(self):
        return self._response_schema(
            next_states=[
                # when we still have lines to process
                "start_line",
                # when the source location is empty
                "zero_check",
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
            ]
        )

    def prepare_unload(self):
        return self._response_schema(
            next_states=[
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
            ]
        )

    def is_zero(self):
        return self._response_schema(
            next_states=[
                # when we still have lines to process
                "start_line",
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
            ]
        )

    def skip_line(self):
        return self._response_schema(next_states=["start_line"])

    def stock_issue(self):
        return self._response_schema(
            next_states=[
                # when we still have lines to process
                "start_line",
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
                "start",
            ]
        )

    def change_pack_lot(self):
        return self._response_schema(next_states=["scan_destination", "start_line"])

    def set_destination_all(self):
        return self._response_schema(
            next_states=[
                # if the batch still contain lines
                "start_line",
                # invalid destination, have to scan a valid one
                "unload_all",
                # this endpoint was called but after checking, lines
                # have different destination locations
                "unload_single",
                # different destination to confirm
                "confirm_unload_all",
                # batch finished
                "start",
            ]
        )

    def unload_split(self):
        return self._response_schema(next_states=["unload_single"])

    def unload_router(self):
        return self._response_schema(
            next_states=["unload_single", "start_line", "start"]
        )

    def unload_scan_pack(self):
        return self._response_schema(
            next_states=["unload_single", "unload_set_destination"]
        )

    def unload_scan_destination(self):
        return self._response_schema(
            next_states=[
                "unload_single",
                "confirm_unload_set_destination",
                "show_completion_info",
                "start",
                "start_line",
            ]
        )

    # TODO single class for sharing schemas between services
    @property
    def _schema_for_batch_details(self):
        return {
            # TODO full name instead of id? or always wrap in batch/move_line?
            # id is a stock.picking.batch
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "pickings": {
                "type": "list",
                "required": True,
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                        "move_line_count": {"required": True, "type": "integer"},
                        "weight": {
                            "type": "float",
                            "nullable": False,
                            "required": True,
                        },
                        "origin": {
                            "type": "string",
                            "nullable": False,
                            "required": True,
                        },
                        "partner": {
                            "type": "dict",
                            "required": False,
                            "nullable": True,
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
            },
        }

    @property
    def _schema_for_single_line_details(self):
        return {
            # id is a stock.move.line
            "id": {"required": True, "type": "integer"},
            "quantity": {"type": "float", "required": True},
            "postponed": {"type": "boolean", "required": False},
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": False, "required": True},
                    "note": {"type": "string", "nullable": False, "required": True},
                    "partner": {
                        "type": "dict",
                        "required": False,
                        "nullable": True,
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
            "batch": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "product": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "display_name": {
                        "type": "string",
                        "nullable": False,
                        "required": True,
                    },
                    "default_code": {
                        "type": "string",
                        "nullable": False,
                        "required": True,
                    },
                    "qty_available": {
                        "type": "float",
                        "nullable": False,
                        "required": True,
                    },
                },
            },
            "lot": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "ref": {"type": "string", "nullable": False, "required": True},
                },
            },
            # TODO share parts of the schema?
            "location_src": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "location_dst": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "pack": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "destination_pack": {
                "type": "dict",
                "required": False,
                "nullable": True,
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }

    @property
    def _schema_for_unload_all(self):
        return {
            # stock.batch.picking
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "location_dst": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }

    @property
    def _schema_for_unload_single(self):
        return {
            # stock.batch.picking
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "package": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "location_dst": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }

    @property
    def _schema_for_zero_check(self):
        return {
            # stock.move.line
            "id": {"required": True, "type": "integer"},
            "location_src": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }

    @property
    def _schema_for_completion_info(self):
        return {
            # stock.picking.batch
            "id": {"required": True, "type": "integer"},
            "picking_done": {"type": "string", "nullable": False, "required": True},
            "picking_next": {"type": "string", "nullable": False, "required": True},
        }

    @property
    def _schema_for_batch_selection(self):
        batch_validator = self.component(usage="picking_batch.validator.response")
        return batch_validator.search()["data"]["schema"]
