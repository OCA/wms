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
        return self._response(state="start")

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

    def find_batch(self):
        return self._response_schema(
            {
                "confirm_start": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_batch_details,
                },
                "start_line": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
                "start": {"type": "dict", "required": False},
            }
        )

    def select(self):
        return self._response_schema(
            {
                "manual_selection": {"type": "dict", "required": False},
                "confirm_start": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
                "start_line": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
            }
        )

    def unassign(self):
        return self._response_schema({"start": {"type": "dict", "required": False}})

    def scan_line(self):
        return self._response_schema(
            {
                "start_line": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
                "scan_destination": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
            }
        )

    def scan_destination_pack(self):
        return self._response_schema(
            # when we still have lines to process
            {
                "start_line": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_single_line_details,
                },
                "zero_check": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_zero_check,
                },
                # when all lines have been processed and have same
                # destination
                "unload_all": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_all,
                },
                # when all lines have been processed and have different
                # destinations
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
            }
        )

    def prepare_unload(self):
        return self._response_schema(
            {
                # when all lines have been processed and have same
                # destination
                "unload_all": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_all,
                },
                # when all lines have been processed and have different
                # destinations
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
            }
        )

    def is_zero(self):
        return self._response_schema(
            {
                # when we still have lines to process
                "start_line": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_single_line_details,
                },
                # when all lines have been processed and have same
                # destination
                "unload_all": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_all,
                },
                # when all lines have been processed and have different
                # destinations
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
            }
        )

    def skip_line(self):
        return self._response_schema(
            {
                "start_line": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                }
            }
        )

    def stock_issue(self):
        return self._response_schema(
            {
                # when we still have lines to process
                "start_line": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_single_line_details,
                },
                # when all lines have been processed and have same
                # destination
                "unload_all": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_all,
                },
                # when all lines have been processed and have different
                # destinations
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
            }
        )

    def change_pack_lot(self):
        return self._response_schema(
            {
                "scan_destination": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                }
            }
        )

    def set_destination_all(self):
        return self._response_schema(
            {
                # if the batch still contain lines
                "start_line": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_single_line_details,
                },
                "confirm_unload_all": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_all,
                },
                "start": {"type": "dict", "required": False},
            }
        )

    def unload_split(self):
        return self._response_schema(
            {
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                }
            }
        )

    def unload_scan_pack(self):
        return self._response_schema(
            {
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
                "unload_set_destination": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
            }
        )

    def unload_scan_destination(self):
        return self._response_schema(
            {
                "unload_confirm_pack": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
                "confirm_unload_set_destination": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
                "show_completion_info": {
                    "type": "dict",
                    "required": False,
                    "schema": self._schema_for_unload_single,
                },
                "start": {"type": "dict", "required": False},
                "start_line": {
                    "type": "dict",
                    "required": True,
                    "schema": self._schema_for_single_line_details,
                },
            }
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
