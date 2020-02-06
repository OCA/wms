from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackPutaway(Component):
    """Methods for the Single Pack Put-Away Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.putaway"
    _usage = "single_pack_putaway"
    _description = __doc__

    def _response_for_no_picking_type(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.no_picking_type())

    def _response_for_several_picking_types(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.several_picking_types())

    def _response_for_package_not_found(self, barcode):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.package_not_found_for_barcode(barcode)
        )

    def _response_for_forbidden_package(self, barcode, picking_type):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.package_not_allowed_in_src_location()
        )

    def _response_for_forbidden_start(self, existing_operations):
        return self._response(
            state="start",
            message={
                "message_type": "error",
                "title": _("Cannot proceed"),
                "message": _(
                    "An operation exists in %s %s. "
                    "You cannot process it with this shopfloor process."
                )
                % (
                    existing_operations[0].picking_id.picking_type_id.name,
                    existing_operations[0].picking_id.name,
                ),
            },
        )

    def _response_for_start_to_confirm(self, existing_operations, pack):
        message = self.actions_for("message")
        move = existing_operations.move_id
        return self._response(
            data={
                "id": existing_operations[0].package_level_id.id,
                "name": pack.name,
                "location_src": {
                    "id": pack.location_id.id,
                    "name": pack.location_id.name,
                },
                "location_dst": {
                    "id": existing_operations[0].location_dest_id.id,
                    "name": existing_operations[0].location_dest_id.name,
                },
                "product": {"id": move.product_id.name, "name": move.product_id.name},
                "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
            },
            state="confirm_start",
            message=message.already_running_ask_confirmation(),
        )

    def _response_for_start_success(self, move, pack):
        message = self.actions_for("message")
        return self._response(
            state="scan_location",
            message=message.scan_destination(),
            data={
                "id": move.move_line_ids[0].package_level_id.id,
                "name": pack.name,
                "location_src": {
                    "id": pack.location_id.id,
                    "name": pack.location_id.name,
                },
                "location_dst": {
                    "id": move.move_line_ids[0].location_dest_id.id,
                    "name": move.move_line_ids[0].location_dest_id.name,
                },
                "product": {"id": move.product_id.id, "name": move.product_id.name},
                "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
            },
        )

    def start(self, barcode):
        """Scan a pack barcode"""

        picking_type = self.picking_types
        if len(picking_type) > 1:
            return self._response_for_several_picking_types()
        elif not picking_type:
            return self._response_for_no_picking_type()

        search = self.actions_for("search")
        pack = search.package_from_scan(barcode)
        if not pack:
            return self._response_for_package_not_found(barcode)
        assert len(pack) == 1, "We cannot have 2 packages with the same barcode"

        # TODO this seems to be a pretty common check, consider moving
        # it to an Action Component
        allowed_locations = self.env["stock.location"].search(
            [("id", "child_of", picking_type.default_location_src_id.id)]
        )
        if pack.location_id not in allowed_locations:
            return self._response_for_forbidden_package(barcode, picking_type)

        quantity = pack.quant_ids[0].quantity
        existing_operations = self.env["stock.move.line"].search(
            [("qty_done", "=", quantity), ("package_id", "=", pack.id)]
        )
        if (
            existing_operations
            and existing_operations[0].picking_id.picking_type_id != picking_type
        ):
            return self._response_for_forbidden_start(existing_operations)
        elif existing_operations:
            return self._response_for_start_to_confirm(existing_operations, pack)

        move_vals = self._prepare_stock_move(picking_type, pack)
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm(merge=False)
        package_level = self._prepare_package_level(pack, move)
        move._action_assign()
        package_level.is_done = True
        return self._response_for_start_success(move, pack)

    def _prepare_stock_move(self, picking_type, pack):
        # FIXME we consider only one product per pack
        assert len(pack.quant_ids) == 1
        product = pack.quant_ids[0].product_id
        default_location_dest = picking_type.default_location_dest_id
        company = self.env.company
        return {
            "picking_type_id": picking_type.id,
            "product_id": product.id,
            "location_id": pack.location_id.id,
            "location_dest_id": default_location_dest.id,
            "name": product.name,
            "product_uom": product.uom_id.id,
            "product_uom_qty": pack.quant_ids[0].quantity,
            "company_id": company.id,
        }

    def _prepare_package_level(self, pack, move):
        return self.env["stock.package_level"].create(
            {
                "package_id": pack.id,
                "move_ids": [(4, move.id)],
                "company_id": self.env.company.id,
                "picking_id": move.picking_id.id,
            }
        )

    def _response_for_package_level_not_found(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.operation_not_found())

    def _response_for_move_canceled_elsewhere(self):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.operation_has_been_canceled_elsewhere()
        )

    def _response_for_location_not_found(self):
        message = self.actions_for("message")
        return self._response(
            state="scan_location", message=message.no_location_found()
        )

    def _response_for_forbidden_location(self):
        message = self.actions_for("message")
        return self._response(
            state="scan_location", message=message.dest_location_not_allowed()
        )

    def _response_for_location_need_confirm(self):
        message = self.actions_for("message")
        return self._response(
            state="confirm_location", message=message.need_confirmation()
        )

    def _response_for_validate_success(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.confirm_pack_moved())

    def validate(self, package_level_id, location_barcode, confirmation=False):
        """Validate the transfer"""
        pack_transfer = self.actions_for("pack.transfer.validate")
        search = self.actions_for("search")

        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response_for_package_level_not_found()

        move = package.move_line_ids[0].move_id
        if not pack_transfer.is_move_state_valid(move):
            return self._response_for_move_canceled_elsewhere()

        scanned_location = search.location_from_scan(location_barcode)
        if not scanned_location:
            return self._response_for_location_not_found()
        if not pack_transfer.is_dest_location_valid(move, scanned_location):
            return self._response_for_forbidden_location()

        if pack_transfer.is_dest_location_to_confirm(move, scanned_location):
            if confirmation:
                # keep the move in sync otherwise we would have a move line outside
                # the dest location of the move
                move.location_dest_id = scanned_location.id
            else:
                return self._response_for_location_need_confirm()

        pack_transfer.set_destination_and_done(move, scanned_location)
        return self._response_for_validate_success()

    def _response_for_move_already_processed(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.already_done())

    def _response_for_confirm_move_cancellation(self):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.confirm_canceled_scan_next_pack()
        )

    def cancel(self, package_level_id):
        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response_for_package_level_not_found()
        # package.move_ids may be empty, it seems
        move = package.move_line_ids.move_id
        if move.state == "done":
            return self._response_for_move_already_processed()

        package.move_line_ids.move_id._action_cancel()
        return self._response_for_confirm_move_cancellation()

    def _validator_cancel(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def _validator_validate(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_barcode": {"type": "string", "nullable": False, "required": True},
        }

    def _validator_return_validate(self):
        return self._response_schema()

    def _validator_start(self):
        return {"barcode": {"type": "string", "nullable": False, "required": True}}

    def _validator_return_start(self):
        return self._response_schema(
            {
                "id": {"coerce": to_int, "required": True, "type": "integer"},
                "name": {"type": "string", "nullable": False, "required": True},
                "location_src": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
                "location_dst": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
                "product": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
                "picking": {
                    "type": "dict",
                    "schema": {
                        "id": {"coerce": to_int, "required": True, "type": "integer"},
                        "name": {"type": "string", "nullable": False, "required": True},
                    },
                },
            }
        )
