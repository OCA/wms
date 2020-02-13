from odoo.addons.base_rest.components.service import to_bool, to_int
from odoo.addons.component.core import Component


class ClusterPicking(Component):
    """Methods for the Cluster Picking Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.cluster.picking"
    _usage = "cluster_picking"
    _description = __doc__

    def find_batch(self):
        """Find a picking batch to work on and start it

        Usually the starting point of the process.
        """
        return self._response()

    def select(self, batch_id):
        """Manually select a picking batch

        The client application can use the service /picking_batch/search
        to get the list of candidate batches.
        """
        return self._response()

    def unassign(self, batch_id):
        """Unassign and reset to draft a started picking batch"""
        return self._response(next_state="start")

    def scan_line(self, move_line_id, barcode):
        """Scan a location, a pack, a product or a lots

        To validate the operator takes the expected pack or product.
        """
        return self._response()

    def scan_destination_pack(self, move_line_id, barcode):
        """Scan the destination pack (bin) for a move line

        It will change the destination of the move line
        """
        return self._response()

    def prepare_unload(self, picking_batch_id):
        """Scan the destination pack (bin) for a move line

        It will change the destination of the move line
        """
        return self._response()

    def is_zero(self, move_line_id, zero):
        """Confirm or not if the source location of a move has zero qty"""
        return self._response()

    def skip_line(self, move_line_id):
        """Skip a line. The line will be processed at the end."""
        return self._response()

    def stock_issue(self, move_line_id):
        """Declare a stock issue for a line"""
        return self._response()

    def change_pack_lot(self, move_line_id, barcode):
        """Change the expected pack or the lot for a line"""
        return self._response()

    def set_destination_all(self, picking_batch_id, barcode, confirmation=False):
        """Set the destination for all the lines of the batch"""
        return self._response()

    def unload_split(self, picking_batch_id, barcode, confirmation=False):
        """Set the destination for all the lines of the batch"""
        return self._response()

    def unload_scan_pack(self, move_line_id, barcode):
        """Check that the operator scans the correct pack (bin)"""
        return self._response()

    def unload_scan_destination(self, move_line_id, barcode, confirmation=False):
        """Check that the operator scans the correct pack (bin)"""
        return self._response()


class ShopfloorClusterPickingValidator(Component):
    """Validators for the Cluster Picking endpoints"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.cluster_picking.validator"
    _usage = "cluster_picking.validator"

    def find_batch(self):
        return {}

    def select(self):
        return {"batch_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def unassign(self):
        return {"batch_id": {"coerce": to_int, "required": True, "type": "integer"}}

    def scan_line(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
        }

    def scan_destination_pack(self):
        return {
            "move_line_id": {"coerce": to_int, "required": True, "type": "integer"},
            "barcode": {"required": True, "type": "string"},
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
            "unload_confirm_pack": self._schema_for_unload_single,
            "unload_set_destination": self._schema_for_unload_single,
            "confirm_unload_set_destination": self._schema_for_unload_single,
            "show_completion_info": self._schema_for_unload_single,
        }

    def find_batch(self):
        return self._response_schema(
            next_states=["confirm_start", "start_line", "start"]
        )

    def select(self):
        return self._response_schema(next_states=["manual_selection", "confirm_start"])

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
                "unload_confirm_pack",
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
                "unload_confirm_pack",
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
                "unload_confirm_pack",
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
                "unload_confirm_pack",
            ]
        )

    def change_pack_lot(self):
        return self._response_schema(next_states=["scan_destination"])

    def set_destination_all(self):
        return self._response_schema(
            next_states=[
                # if the batch still contain lines
                "start_line",
                # different destination to confirm
                "confirm_unload_all",
                # batch finished
                "start",
            ]
        )

    def unload_split(self):
        return self._response_schema(next_states=["unload_confirm_pack"])

    def unload_scan_pack(self):
        return self._response_schema(
            next_states=["unload_confirm_pack", "unload_set_destination"]
        )

    def unload_scan_destination(self):
        return self._response_schema(
            next_states=[
                "unload_confirm_pack",
                "confirm_unload_set_destination",
                "show_completion_info",
                "start",
                "start_line",
            ]
        )

    @property
    def _schema_for_batch_details(self):
        return {
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
