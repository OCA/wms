# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from functools import reduce

from odoo import _, fields
from odoo.osv import expression

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component

from .exception import (
    BarcodeNotFoundError,
    BatchDoesNotExistError,
    DestLocationNotAllowed,
    OperationNotFoundError,
    ProductNotInSource,
    TooMuchProductInCommandError,
    UnableToPickMoreError,
    response_decorator,
)


class ClusterBatchPicking(Component):
    """
    Cluster Batch Picking Process
    The goal of this scenario is to do the pickings for
    several customers at once. Orders can be mixed together in
    this scenario (difference with Cluster Picking).
    """

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.cluster.batch_picking"
    _usage = "cluster_batch_picking"
    _description = __doc__

    @staticmethod
    def _sort_key_lines(line):
        return (
            line.shopfloor_priority or 10,
            line.location_id.shopfloor_picking_sequence or "",
            line.location_id.name,
            -int(line.move_id.priority or 1),
            line.move_id.date_expected,
            line.move_id.sequence,
            line.move_id.id,
            line.id,
        )

    def _batch_filter(self, batch):
        if not batch.picking_ids:
            return False
        return batch.picking_ids.filtered(self._batch_picking_filter)

    def _batch_picking_filter(self, picking):
        # Picking type guard
        if picking.picking_type_id not in self.picking_types:
            return False
        # Include done/cancel because we want to be able to work on the
        # batch even if some pickings are done/canceled. They'll should be
        # ignored later.
        # When the batch is already in progress, we do not care
        # about state of the pickings, because we want to be able
        # to recover it in any case, even if, for instance, a stock
        # error changed a picking to unavailable after the user
        # started to work on the batch.
        return picking.batch_id.state == "in_progress" or picking.state in (
            "assigned",
            "done",
            "cancel",
        )

    def _get_lines_to_pick(self, move_lines):
        return move_lines.filtered(
            lambda l: (
                l.state in ("assigned", "partially_available")
                # On 'StockPicking.action_assign()', result_package_id is set to
                # the same package as 'package_id'. Here, we need to exclude lines
                # that were already put into a bin, i.e. the destination package
                # is different.
                and (not l.result_package_id or l.result_package_id == l.package_id)
                and (l.picking_id.location_dest_id == l.location_dest_id)
            ),
        ).sorted(key=self._sort_key_lines)

    def _get_batch(self, picking_batch_id):
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            raise BatchDoesNotExistError
        return batch

    def _get_move_line(self, move_line_id, next_state, data):
        move_line = self.env["stock.move.line"].browse(move_line_id)
        if not move_line.exists():
            raise OperationNotFoundError(
                state=next_state, data=data,
            )
        return move_line

    def _next_line_for_pick(self, move_lines):
        remaining_lines = self._get_lines_to_pick(move_lines)
        return fields.first(remaining_lines)

    def _create_data_for_scan_products(
        self, move_lines, batch,
    ):
        picking_destination = {}
        for picking in batch.picking_ids:
            picking_destination[picking.id] = {}

            suggested_location_dest = []
            suggested_package_dest = []

            for line_in_picking in picking.move_line_ids:
                if (
                    line_in_picking.location_dest_id
                    and line_in_picking.location_dest_id != picking.location_dest_id
                ):
                    suggested_location_dest.append(
                        self.data.location(line_in_picking.mapped("location_dest_id"))
                    )
                if line_in_picking.result_package_id:
                    suggested_package_dest.append(
                        self.data.package(line_in_picking.mapped("result_package_id"))
                    )

            suggested_package_dest = reduce(
                lambda l, x: l.append(x) or l if x not in l else l,
                suggested_package_dest,
                [],
            )
            suggested_location_dest = reduce(
                lambda l, x: l.append(x) or l if x not in l else l,
                suggested_location_dest,
                [],
            )

            picking_destination[picking.id][
                "suggested_package_dest"
            ] = suggested_package_dest
            picking_destination[picking.id][
                "suggested_location_dest"
            ] = suggested_location_dest

        move_lines_data = self.data.move_lines(
            move_lines, with_picking=True, with_packaging=True
        )
        for line in move_lines_data:
            picking = line["picking"]
            line.update(picking_destination[picking["id"]])

        return {
            "move_lines": move_lines_data,
            "id": batch.id,
        }

    def _are_all_dest_location_same(self, batch):
        lines_to_unload = self._lines_to_unload(batch)
        return len(lines_to_unload.mapped("location_dest_id")) == 1

    def _lines_to_unload(self, batch):
        return self._lines_for_picking_batch(batch, filter_func=self._filter_for_unload)

    def _lines_for_picking_batch(self, picking_batch, filter_func=lambda x: x):
        lines = picking_batch.mapped("picking_ids.move_line_ids").filtered(filter_func)
        # TODO test line sorting and all these methods to retrieve lines

        # Sort line by source location,
        # so that the picker start w/ products in the same location.
        # Postponed lines must come always
        # after ALL the other lines in the batch are processed.
        return lines.sorted(key=self._sort_key_lines)

    def _filter_for_unload(self, line):
        return (
            line.state in ("assigned", "partially_available")
            and line.qty_done > 0
            and line.result_package_id
            and not line.shopfloor_unloaded
        )

    def _unload_next_package(self, batch, completion_info_popup=None):
        next_package = self._next_bin_package_for_unload_single(batch)
        if next_package:
            return self._response_for_unload_single(
                batch, next_package, popup=completion_info_popup
            )
        return self._unload_end(batch, completion_info_popup=completion_info_popup)

    def _next_bin_package_for_unload_single(self, batch):
        packages = self._bin_packages_to_unload(batch)
        return fields.first(packages)

    def _bin_packages_to_unload(self, batch):
        lines = self._lines_to_unload(batch)
        packages = lines.mapped("result_package_id").sorted()
        return packages

    def _response_for_unload_all(self, batch, message=None):
        return self._response(
            next_state="unload_all",
            data=self._data_for_unload_all(batch),
            message=message,
        )

    def _data_for_unload_all(self, batch):
        lines = self._lines_to_unload(batch)
        # all the lines destinations are the same here, it looks
        # only for the first one
        first_line = fields.first(lines)
        data = self.data.picking_batch(batch, with_pickings=True)
        data.update({"location_dest": self.data.location(first_line.location_dest_id)})
        return data

    def _response_for_unload_single(self, batch, package, message=None, popup=None):
        return self._response(
            next_state="unload_single",
            data=self._data_for_unload_single(batch, package),
            message=message,
            popup=popup,
        )

    def _data_for_unload_single(self, batch, package):
        line = fields.first(
            package.planned_move_line_ids.filtered(self._filter_for_unload)
        )
        data = self.data.picking_batch(batch)
        data.update(
            {
                "package": self.data.package(package),
                "location_dest": self.data.location(line.location_dest_id),
            }
        )
        return data

    def _unload_end(self, batch, completion_info_popup=None):
        """Try to close the batch if all transfers are done.

        Returns to `start_line` transition if some lines could still be processed,
        otherwise try to validate all the transfers of the batch.
        """
        if all(picking.state == "done" for picking in batch.picking_ids):
            # do not use the 'done()' method because it does many things we
            # don't care about
            batch.state = "done"
            return self._response_for_start(
                message=self.msg_store.batch_transfer_complete(),
                popup=completion_info_popup,
            )

        next_line = self._next_line_for_pick(batch)
        if next_line:
            return self._response_for_start_line(
                next_line,
                message=self.msg_store.batch_transfer_line_done(),
                popup=completion_info_popup,
            )
        else:
            # TODO add tests for this (for instance a picking is not 'done'
            # because a move was unassigned, we want to validate the batch to
            # produce backorders)
            batch.mapped("picking_ids")._action_done()
            batch.state = "done"
            # Unassign not validated pickings from the batch, they will be
            # processed in another batch automatically later on
            pickings_not_done = batch.mapped("picking_ids").filtered(
                lambda p: p.state != "done"
            )
            pickings_not_done.batch_id = False
            return self._response_for_start(
                message=self.msg_store.batch_transfer_complete(),
                popup=completion_info_popup,
            )

    def _batch_picking_base_search_domain(self):
        return [
            "|",
            "&",
            ("user_id", "=", False),
            ("state", "=", "draft"),
            "&",
            ("user_id", "=", self.env.user.id),
            ("state", "in", ("draft", "in_progress")),
        ]

    def _batch_picking_search(self, name_fragment=None, batch_ids=None):
        domain = self._batch_picking_base_search_domain()
        if name_fragment:
            domain = expression.AND([domain, [("name", "ilike", name_fragment)]])
        if batch_ids:
            domain = expression.AND([domain, [("id", "in", batch_ids)]])
        records = self.env["stock.picking.batch"].search(domain, order="id asc")
        records = records.filtered(self._batch_filter)
        return records

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

    def _set_quantity_for_move_line(
        self,
        move_lines,
        batch,
        product,
        move_line,
        quantity_to_set,
        message=None,
        next_state="scan_products",
        data=None,
    ):
        if data is None:
            data = {}

        if product and move_line.product_id == product:
            if quantity_to_set > move_line.product_uom_qty:
                raise TooMuchProductInCommandError(
                    state=next_state, data=data,
                )

            move_line.qty_done = quantity_to_set

            return self._response_for_scan_products(move_lines, batch, message)
        else:
            raise BarcodeNotFoundError(
                state=next_state, data=data,
            )

    def _unload_write_destination_on_lines(self, lines, location):
        lines.write({"shopfloor_unloaded": True, "location_dest_id": location.id})
        lines.package_level_id.location_dest_id = location
        for line in lines:
            # We set the picking to done only when the last line is
            # unloaded to avoid backorders.
            picking = line.picking_id
            if picking.state == "done":
                continue
            picking_lines = picking.mapped("move_line_ids")
            if all(l.shopfloor_unloaded for l in picking_lines):
                picking.action_done()

    def _response_for_manual_selection(self, batches, message=None):
        data = {
            "records": self.data.picking_batches(batches),
            "size": len(batches),
        }
        return self._response(next_state="manual_selection", data=data, message=message)

    def _response_for_confirm_unload_all(self, batch, message=None):
        return self._response(
            next_state="confirm_unload_all",
            data=self._data_for_unload_all(batch),
            message=message,
        )

    def _response_for_start_line(self, move_line, message=None, popup=None):

        return self._response(
            next_state="start_line",
            data=self._data_move_line(move_line),
            message=message,
            popup=popup,
        )

    def _response_for_start(self, message=None, popup=None):
        return self._response(next_state="start", message=message, popup=popup)

    def _response_for_confirm_start(self, batch):
        return self._response(
            next_state="confirm_start",
            data=self.data.picking_batch(batch, with_pickings=True),
        )

    def _response_for_scan_products(self, move_lines, batch, message=None):
        next_line = self._next_line_for_pick(move_lines)

        if not next_line:
            return self.prepare_unload(batch.id)

        return self._response(
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch),
            message=message,
        )

    def _response_batch_does_not_exist(self):
        return self._response_for_start(message=self.msg_store.record_not_found())

    @response_decorator
    def find_batch(self):
        """Find a picking batch to work on and start it

        Usually the starting point of the scenario.

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
        batches = self._batch_picking_search()
        selected = self._select_a_picking_batch(batches)
        if selected:
            return self._response(
                next_state="confirm_start",
                data=self.data.picking_batch(selected, with_pickings=True),
            )
        else:
            return self._response(
                next_state="start",
                message={
                    "message_type": "info",
                    "body": _("No more work to do, please create a new batch transfer"),
                },
            )

    @response_decorator
    def scan_product(self, picking_batch_id, move_line_id, location_id, barcode):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id,
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch,),
        )

        if move_line.location_id.id != location_id:
            raise ProductNotInSource(
                state="scan_products",
                data=self._create_data_for_scan_products(move_lines, batch,),
            )

        search = self._actions_for("search")

        product = search.product_from_scan(barcode)
        quantity_to_set = move_line.qty_done + 1

        return self._set_quantity_for_move_line(
            move_lines,
            batch,
            product,
            move_line,
            quantity_to_set,
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch,),
        )

    @response_decorator
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
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")

        return self._response_for_scan_products(move_lines, batch)

    @response_decorator
    def set_quantity(self, picking_batch_id, move_line_id, location_id, barcode, qty):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id,
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch,),
        )

        search = self._actions_for("search")

        product = search.product_from_scan(barcode)

        if move_line.location_id.id != location_id:
            raise ProductNotInSource(
                state="scan_products",
                data=self._create_data_for_scan_products(move_lines, batch,),
            )

        return self._set_quantity_for_move_line(
            move_lines,
            batch,
            product,
            move_line,
            qty,
            next_state="scan_products",
            data=self._create_data_for_scan_products(move_lines, batch,),
        )

    @response_decorator
    def set_destination(self, picking_batch_id, move_line_id, barcode, qty):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id, next_state="scan_products", data="move_lines"
        )

        search = self._actions_for("search")

        location_dest = search.location_from_scan(barcode)
        bin_package = search.package_from_scan(barcode)

        if not location_dest and not bin_package:
            raise BarcodeNotFoundError(
                state="scan_products",
                data=self._create_data_for_scan_products(move_lines, batch,),
            )

        if location_dest.id is move_line.location_id.id:
            product = move_line.mapped("product_id")
            return self._set_quantity_for_move_line(
                move_lines,
                batch,
                product,
                move_line,
                0,
                message={
                    "message_type": "success",
                    "body": "Product put back in place",
                },
                next_state="scan_products",
                data=self._create_data_for_scan_products(move_lines, batch,),
            )

        new_line, qty_check = move_line._split_qty_to_be_done(qty)

        if qty_check == "greater":
            raise UnableToPickMoreError(
                state="scan_products",
                data=self._create_data_for_scan_products(move_lines, batch,),
                quantity=move_line.product_uom_qty,
            )

        if location_dest:
            if not location_dest.is_sublocation_of(
                move_line.picking_id.location_dest_id
            ):
                raise DestLocationNotAllowed(
                    state="scan_products",
                    data=self._create_data_for_scan_products(move_lines, batch,),
                )

            move_line.write({"qty_done": qty, "location_dest_id": location_dest.id})
            move_line.shopfloor_checkout_done = True

            return self._response_for_scan_products(
                batch.mapped("picking_ids.move_line_ids"),
                batch,
                message=self.msg_store.x_units_put_in_location(
                    move_line.qty_done, move_line.product_id, location_dest
                ),
            )

        if bin_package:
            move_line.write({"qty_done": qty, "result_package_id": bin_package.id})
            move_line.shopfloor_checkout_done = True

            return self._response_for_scan_products(
                batch.mapped("picking_ids.move_line_ids"),
                batch,
                message=self.msg_store.x_units_put_in_package(
                    move_line.qty_done,
                    move_line.product_id,
                    move_line.result_package_id,
                ),
            )

    @response_decorator
    def prepare_unload(self, picking_batch_id):
        """Initiate the unloading phase of the scenario

        It goes to different screens depending if all the move lines have
        the same destination or not.

        Transitions:
        * unload_all: when all lines go to the same destination
        * unload_single: when lines have different destinations
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            return self._response_batch_does_not_exist()
        if self._are_all_dest_location_same(batch):
            return self._response_for_unload_all(batch)
        else:
            # the lines have different destinations
            return self._unload_next_package(batch)

    @response_decorator
    def cancel_line(self, picking_batch_id, move_line_id):
        batch = self._get_batch(picking_batch_id)
        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")
        move_line = self._get_move_line(
            move_line_id, next_state="scan_products", data="move_lines"
        )

        move_line.qty_done = 0
        move_line.shopfloor_checkout_done = False
        move_line.result_package_id = None
        move_line.location_dest_id = move_line.picking_id.location_dest_id

        return self._response_for_scan_products(move_lines, batch,)

    @response_decorator
    def list_batch(self):
        """List picking batch on which user can work

        Returns a list of all the available records for the current picking
        type.

        Transitions:
        * manual_selection: to the selection screen
        """
        batches = self._batch_picking_search()
        return self._response_for_manual_selection(batches)

    @response_decorator
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
        batches = self._batch_picking_search(batch_ids=[picking_batch_id])
        selected = self._select_a_picking_batch(batches)
        if selected:
            return self._response_for_confirm_start(selected)
        else:
            return self._response(
                base_response=self.list_batch(),
                message={
                    "message_type": "warning",
                    "body": _("This batch cannot be selected."),
                },
            )

    @response_decorator
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
          to handle the closing of the batch to create backorders.
        """
        batch = self.env["stock.picking.batch"].browse(picking_batch_id)
        if not batch.exists():
            raise BatchDoesNotExistError

        # In case /set_destination_all was called and the destinations were
        # in fact no the same... restart the unloading step over
        if not self._are_all_dest_location_same(batch):
            return self.prepare_unload(batch.id)

        lines = self._lines_to_unload(batch)
        if not lines:
            return self._unload_end(batch)

        first_line = fields.first(lines)
        picking_type = fields.first(batch.picking_ids).picking_type_id
        scanned_location = self._actions_for("search").location_from_scan(barcode)
        if not scanned_location:
            return self._response_for_unload_all(
                batch, message=self.msg_store.no_location_found()
            )
        if not scanned_location.is_sublocation_of(
            picking_type.default_location_dest_id
        ) or not scanned_location.is_sublocation_of(
            lines.mapped("move_id.location_dest_id"), func=all
        ):
            return self._response_for_unload_all(
                batch, message=self.msg_store.dest_location_not_allowed()
            )

        if not scanned_location.is_sublocation_of(first_line.location_dest_id):
            if not confirmation:
                return self._response_for_confirm_unload_all(batch)

        self._unload_write_destination_on_lines(lines, scanned_location)
        completion_info = self._actions_for("completion.info")
        completion_info_popup = completion_info.popup(lines)
        return self._unload_end(batch, completion_info_popup=completion_info_popup)

    @response_decorator
    def stock_issue(self, picking_batch_id, move_line_id):
        """Declare a stock issue for a line

        After errors in the stock, the user cannot take all the products
        because there is physically not enough goods. The move line is deleted
        (unreserve), and an inventory is created to reduce the quantity in the
        source location to prevent future errors until a correction. Beware:
        the quantity already reserved by other lines should remain reserved so
        the inventory's quantity must be set to the quantity of lines reserved
        by other move lines (but not the current one).

        The other lines not yet picked in the batch for the same product, lot,
        package are unreserved as well (moves lines deleted, which unreserve
        their quantity on the move).

        A second inventory is created in draft to have someone do an inventory
        check.

        Transitions:
        * start_line: when the batch still contains lines without destination
          package
        * unload_all: if all lines have a destination package and same
          destination
        * unload_single: if all lines have a destination package and different
          destination
        * start: all lines are done/confirmed (because all lines were unloaded
          and the last line has a stock issue). In this case, this method *has*
          to handle the closing of the batch to create backorders (_unload_end)
        """
        batch = self._get_batch(picking_batch_id)
        move_line = self._get_move_line(
            move_line_id, next_state="scan_products", data="move_lines"
        )

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

        # unreserve every lines for the same product/lot in the same batch and
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

        pickings = batch.mapped("picking_ids")
        move_lines = pickings.mapped("move_line_ids")

        return self._response_for_scan_products(
            move_lines,
            batch,
            message=self.msg_store.stock_issue_for_line(move.product_id.name,),
        )

    def _domain_stock_issue_unlink_lines(self, move_line):
        # Since we have not enough stock, delete the move lines, which will
        # in turn unreserve the moves. The moves lines we delete are those
        # in the same batch (we don't want to interfere with other operators
        # work, they'll have to declare a stock issue), and not yet started.
        # The goal is to prevent the same operator to declare twice the same
        # stock issue for the same product/lot/package.
        batch = move_line.picking_id.batch_id
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
            ("picking_id.batch_id", "=", batch.id),
        ]
        return domain


class ShopfloorClusterBatchPickingValidator(Component):
    """Validators for the Cluster Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.cluster_batch_picking.validator"
    _usage = "cluster_batch_picking.validator"

    def find_batch(self):
        return {}

    def confirm_start(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def set_quantity(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def scan_product(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def set_destination(self):
        return {
            "barcode": {"required": True, "type": "string"},
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "qty": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def list_batch(self):
        return {}

    def select(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def cancel_line(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }

    def prepare_unload(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def set_destination_all(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }

    def stock_issue(self):
        return {
            "picking_batch_id": {"coerce": to_int, "required": True, "type": "integer"},
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
        }


class ShopfloorClusterPickingValidatorResponse(Component):
    """Validators for the Cluster Picking endpoints responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.cluster_batch_picking.validator.response"
    _usage = "cluster_batch_picking.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "confirm_start": self._schema_for_batch_details,
            "confirm_unload_all": self._schema_for_unload_all,
            "manual_selection": self._schema_for_batch_selection,
            "scan_products": self._schema_for_move_lines_details,
            "start": {},
            "unload_all": self._schema_for_unload_all,
            "unload_single": self._schema_for_unload_single,
        }

    def find_batch(self):
        return self._response_schema(next_states={"confirm_start"})

    def set_quantity(self):
        return self._response_schema(next_states={"scan_products"})

    def set_destination(self):
        return self._response_schema(
            next_states={"unload_all", "unload_single", "scan_products"}
        )

    def scan_product(self):
        return self._response_schema(next_states={"scan_products"})

    def confirm_start(self):
        return self._response_schema(
            next_states={
                # we reopen a batch already started where all the lines were
                # already picked and have to be unloaded to the same
                # destination
                "unload_all",
                # we reopen a batch already started where all the lines were
                # already picked and have to be unloaded to the different
                # destinations
                "unload_single",
                "scan_products",
            }
        )

    def prepare_unload(self):
        return self._response_schema(
            next_states={
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
            }
        )

    def cancel_line(self):
        return self._response_schema(next_states={"scan_products"})

    def set_destination_all(self):
        return self._response_schema(
            next_states={"unload_all", "confirm_unload_all", "start"}
        )

    def stock_issue(self):
        return self._response_schema(
            next_states={
                # when we still have lines to process
                "scan_products",
                # when all lines have been processed and have same
                # destination
                "unload_all",
                # when all lines have been processed and have different
                # destinations
                "unload_single",
            }
        )

    def list_batch(self):
        return self._response_schema(next_states={"manual_selection"})

    def select(self):
        return self._response_schema(next_states={"manual_selection", "confirm_start"})

    @property
    def _schema_for_move_lines_details(self):
        return {
            "move_lines": self.schemas._schema_list_of(
                self.schemas.move_line(with_packaging=True, with_picking=True)
            ),
            "id": {"required": True, "type": "integer"},
        }

    @property
    def _schema_for_batch_details(self):
        return self.schemas.picking_batch(with_pickings=True)

    @property
    def _schema_for_batch_selection(self):
        return self.schemas._schema_search_results_of(self.schemas.picking_batch())

    @property
    def _schema_for_unload_all(self):
        schema = self.schemas.picking_batch()
        schema["location_dest"] = self.schemas._schema_dict_of(self.schemas.location())
        return schema

    @property
    def _schema_for_unload_single(self):
        schema = self.schemas.picking_batch()
        schema["package"] = self.schemas._schema_dict_of(self.schemas.package())
        schema["location_dest"] = self.schemas._schema_dict_of(self.schemas.location())
        return schema
