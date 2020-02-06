from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackTransfer(Component):
    """Methods for the Single Pack Transfer Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.transfer"
    _usage = "single_pack_transfer"
    _description = __doc__

    def _response_for_empty_location(self, location):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.no_pack_in_location(location)
        )

    def _response_for_several_packages(self, location):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.several_packs_in_location(location)
        )

    def _response_for_package_not_found(self, barcode):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.package_not_found_for_barcode(barcode)
        )

    def _response_for_operation_not_found(self, pack):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.no_pending_operation_for_pack(pack)
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
        search = self.actions_for("search")

        location = search.location_from_scan(barcode)

        pack = self.env["stock.quant.package"]
        if location:
            pack = self.env["stock.quant.package"].search(
                [("location_id", "=", location.id)]
            )
            if not pack:
                return self._response_for_empty_location(location)
            if len(pack) > 1:
                return self._response_for_several_packages(self, location)

        if not pack:
            pack = search.package_from_scan(barcode)

        if not pack:
            return self._response_for_package_not_found(barcode)

        existing_operations = self.env["stock.move.line"].search(
            [
                ("package_id", "=", pack.id),
                ("picking_id.picking_type_id", "in", self.picking_types.ids),
            ]
        )
        if not existing_operations:
            return self._response_for_operation_not_found(pack)
        move = existing_operations.move_id
        if existing_operations[0].package_level_id.is_done:
            return self._response_for_start_to_confirm(existing_operations, pack)

        existing_operations[0].package_level_id.is_done = True
        return self._response_for_start_success(move, pack)

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

    def _response_for_package_level_not_found(self):
        message = self.actions_for("message")
        return self._response(state="start", message=message.operation_not_found())

    def _response_for_move_canceled(self):
        message = self.actions_for("message")
        return self._response(
            state="start", message=message.operation_has_been_canceled_elsewhere()
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
            return self._response_for_move_canceled()

        scanned_location = search.location_from_scan(location_barcode)
        if not pack_transfer.is_dest_location_valid(move, scanned_location):
            return self._response_for_forbidden_location()

        if pack_transfer.is_dest_location_to_confirm(move, scanned_location):
            if confirmation:
                # keep the move in sync otherwise we would have a move line outside
                # the dest location of the move
                move.location_dest_id = scanned_location.id
            else:
                return self._response_for_location_need_confirm()

        pack_transfer.set_destination_and_done()
        return self._response_for_validate_success()

    def _validator_validate(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "boolean", "required": False},
        }

    def _validator_return_validate(self):
        return self._response_schema()

    # TODO cancel
