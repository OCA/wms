from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component

from .service import to_float


class ClusterPicking(Component):
    """Methods for the Cluster Picking Process

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
    * Otherwise, the user has to scan one destination per good.
    * If all the goods are supposed to go to the same destination but user doesn't
      want or can't, a "split" allows to reach the screen to scan one destination
      per good.
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

        a. Find an batch in progress assigned to the current user
        b. Find a draft batch assigned to the current user:
          1. set it to 'in progress'
        c. Find an unassigned draft batch:
          1. assign batch to the current user
          2. set it to 'in progress'

        Transitions:
        * confirm_start: when it could find a batch
        * start: when no batch is available
        """
        return self._response()

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
        return self._response()

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
        return self._response()

    def unassign(self, picking_batch_id):
        """Unassign and reset to draft a started picking batch

        Transitions:
        * "start" to work on a new batch
        """
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
        return self._response()

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
        return self._response()

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
        return self._response()

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
        return self._response()

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
        """Set the destination for all the lines with a dest. package of the batch

        This method must be used only if all the move lines which have a destination
        package and qty done have the same destination location.

        A scanned location outside of the source location of the operation type is
        invalid.

        TODO: remove the destination package or not?

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
        return self._response()

    def unload_split(self, picking_batch_id, barcode, confirmation=False):
        """Indicates that now the batch must be treated line per line

        Even if the move lines to unload all have the same destination.

        It sets the flag ``stock_picking_batch.cluster_picking_unload_all`` to
        False.

        Note: if we go back to the first phase of picking and start a new
        phase of unloading, the flag is reevaluated to the initial condition.

        Transitions:
        * unload_single: always goes here since we now want to unload line per line
        """
        return self._response()

    def unload_router(self, picking_batch_id):
        """Called after the info screen, route to the next state

        No side effect in Odoo.

        Transitions:
        * unload_single: if the batch still has lines to unload
        * start_line: if the batch still has lines to pick
        * start: if the batch is done. In this case, this method *has*
          to handle the closing of the batch to create backorders. TODO find a
          generic way to share actions happening on transitions such as "close
          the batch"
        """
        return self._response()

    def unload_scan_pack(self, move_line_id, barcode):
        """Check that the operator scans the correct package (bin) on unload

        If the package is different as the destination package of the move line,
        ask to scan it again.

        Transitions:
        * unload_single: if the barcode does not match
        * unload_set_destination: barcode is correct
        """
        return self._response()

    def unload_scan_destination(self, move_line_id, barcode, confirmation=False):
        """Scan the final destination of the move line

        TODO not sure. We have to call action_done on the picking *only when we
        have scanned all the move lines* of the picking, so maybe we have to
        keep track of this with a new flag on move lines?

        Transitions:
        * unload_single: invalid scanned location or error
        * unload_single: line is processed and the next line can be unloaded
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
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
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
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def unload_scan_destination(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
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
            "manual_selection": {},
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
            "weight": {"type": "float", "nullable": False, "required": True},
            "pickings": {
                "type": "list",
                "required": True,
                "schema": {
                    "type": "dict",
                    "schema": {
                        "id": {"required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                        "move_line_count": {"required": True, "type": "integer"},
                        "origin": {
                            "type": "string",
                            "nullable": False,
                            "required": True,
                        },
                        "partner": {
                            "type": "dict",
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
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "origin": {"type": "string", "nullable": False, "required": True},
                    "note": {"type": "string", "nullable": False, "required": True},
                },
            },
            "batch": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "quantity": {"type": "float", "required": True},
            "product": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                    "ref": {"type": "string", "nullable": False, "required": True},
                    "qty_available": {
                        "type": "float",
                        "nullable": False,
                        "required": True,
                    },
                },
            },
            "lot": {
                "type": "dict",
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
            # stock.move.line
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
