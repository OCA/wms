from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackPutaway(Component):
    """Methods for the Single Pack Put-Away Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.putaway"
    _usage = "single_pack_putaway"
    _description = __doc__

    # TODO think about not sending back the state when we already
    # come from the same state
    def _response_for_no_picking_type(self):
        message = self.actions_for("message")
        return self._response(next_state="start", message=message.no_picking_type())

    def _response_for_several_picking_types(self):
        message = self.actions_for("message")
        return self._response(
            next_state="start", message=message.several_picking_types()
        )

    def _response_for_package_not_found(self, barcode):
        message = self.actions_for("message")
        return self._response(
            next_state="start", message=message.package_not_found_for_barcode(barcode)
        )

    def _response_for_forbidden_package(self, barcode, picking_type):
        message = self.actions_for("message")
        return self._response(
            next_state="start",
            message=message.package_not_allowed_in_src_location(barcode, picking_type),
        )

    def _response_for_forbidden_start(self, existing_operations):
        return self._response(
            next_state="start",
            message={
                "message_type": "error",
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

    def _data_after_package_scanned(self, move_line, pack):
        move = move_line.move_id
        return {
            "id": move_line.package_level_id.id,
            "name": pack.name,
            "location_src": {"id": pack.location_id.id, "name": pack.location_id.name},
            "location_dst": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
            "product": {"id": move.product_id.id, "name": move.product_id.name},
            "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
        }

    def _response_for_start_to_confirm(self, move_line, pack):
        message = self.actions_for("message")
        return self._response(
            data=self._data_after_package_scanned(move_line, pack),
            next_state="confirm_start",
            message=message.already_running_ask_confirmation(),
        )

    def _response_for_start_success(self, move_line, pack):
        message = self.actions_for("message")
        return self._response(
            next_state="scan_location",
            message=message.scan_destination(),
            data=self._data_after_package_scanned(move_line, pack),
        )

    def start(self, barcode):
        """Scan a pack barcode"""

        picking_type = self.picking_type
        if len(picking_type) > 1:
            return self._response_for_several_picking_types()
        elif not picking_type:
            return self._response_for_no_picking_type()

        search = self.actions_for("search")
        pack = search.package_from_scan(barcode)
        if not pack:
            return self._response_for_package_not_found(barcode)
        assert len(pack) == 1, "We cannot have 2 packages with the same barcode"

        location_src = picking_type.default_location_src_id
        assert location_src, "Picking type has no default source location"

        if not pack.location_id.is_sublocation_of(location_src):
            return self._response_for_forbidden_package(barcode, picking_type)

        existing_operation = self.env["stock.move.line"].search(
            [
                ("package_id", "=", pack.id),
                (
                    "state",
                    "in",
                    (
                        "assigned",
                        "draft",
                        "waiting",
                        "confirmed",
                        "partially_available",
                    ),
                ),
            ],
            limit=1,
        )
        if (
            existing_operation
            and existing_operation[0].picking_id.picking_type_id != picking_type
        ):
            return self._response_for_forbidden_start(existing_operation)
        elif existing_operation:
            return self._response_for_start_to_confirm(existing_operation, pack)

        move_vals = self._prepare_stock_move(picking_type, pack)
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm(merge=False)
        package_level = self._prepare_package_level(pack, move)
        move._action_assign()
        package_level.is_done = True
        # TODO what if we have > 1 move line?
        return self._response_for_start_success(move.move_line_ids, pack)

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
        return self._response(next_state="start", message=message.operation_not_found())

    def _response_for_move_canceled_elsewhere(self):
        message = self.actions_for("message")
        return self._response(
            next_state="start", message=message.operation_has_been_canceled_elsewhere()
        )

    def _response_for_location_not_found(self, move_line, pack):
        message = self.actions_for("message")
        return self._response(
            next_state="scan_location",
            message=message.no_location_found(),
            data=self._data_after_package_scanned(move_line, pack),
        )

    def _response_for_forbidden_location(self, move_line, pack):
        message = self.actions_for("message")
        return self._response(
            next_state="scan_location",
            message=message.dest_location_not_allowed(),
            data=self._data_after_package_scanned(move_line, pack),
        )

    def _response_for_location_need_confirm(self, move_line, pack, to_location):
        message = self.actions_for("message")
        return self._response(
            next_state="confirm_location",
            message=message.confirm_location_changed(
                move_line.location_dest_id, to_location
            ),
            data=self._data_after_package_scanned(move_line, pack),
        )

    def _response_for_validate_success(self):
        message = self.actions_for("message")
        return self._response(next_state="start", message=message.confirm_pack_moved())

    def validate(self, package_level_id, location_barcode, confirmation=False):
        """Validate the transfer"""
        pack_transfer = self.actions_for("pack.transfer.validate")
        search = self.actions_for("search")

        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response_for_package_level_not_found()

        move_line = package.move_line_ids[0]
        move = move_line.move_id
        if not pack_transfer.is_move_state_valid(move):
            return self._response_for_move_canceled_elsewhere()

        scanned_location = search.location_from_scan(location_barcode)
        if not scanned_location:
            return self._response_for_location_not_found(move_line, package.package_id)
        if not pack_transfer.is_dest_location_valid(move, scanned_location):
            return self._response_for_forbidden_location(move_line, package.package_id)

        if pack_transfer.is_dest_location_to_confirm(move, scanned_location):
            if confirmation:
                # If the destination of the move would be incoherent
                # (move line outside of it), we change the moves' destination
                if not scanned_location.is_sublocation_of(move.location_dest_id):
                    move.location_dest_id = scanned_location.id
            else:
                return self._response_for_location_need_confirm(
                    move_line, package.package_id, scanned_location
                )

        pack_transfer.set_destination_and_done(move, scanned_location)
        return self._response_for_validate_success()

    def _response_for_move_already_processed(self):
        message = self.actions_for("message")
        return self._response(next_state="start", message=message.already_done())

    def _response_for_confirm_move_cancellation(self):
        message = self.actions_for("message")
        return self._response(
            next_state="start", message=message.confirm_canceled_scan_next_pack()
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


class SinglePackPutawayValidator(Component):
    """Validators for Single Pack Putaway methods"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.single.pack.putaway.validator"
    _usage = "single_pack_putaway.validator"

    def start(self):
        return {"barcode": {"type": "string", "nullable": False, "required": True}}

    def cancel(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def validate(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "boolean", "nullable": True, "required": False},
        }


class SinglePackPutawayValidatorResponse(Component):
    """Validators for Single Pack Putaway methods responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.single.pack.putaway.validator.response"
    _usage = "single_pack_putaway.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        return {
            "start": {},
            "confirm_start": self._schema_for_location,
            "scan_location": self._schema_for_location,
            "confirm_location": self._schema_for_location,
        }

    def cancel(self):
        return self._response_schema(next_states=["start"])

    def validate(self):
        return self._response_schema(
            next_states=["scan_location", "start", "confirm_location"]
        )

    def start(self):
        return self._response_schema(
            next_states=["confirm_start", "start", "scan_location"]
        )

    @property
    def _schema_for_location(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
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
            "product": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
            "picking": {
                "type": "dict",
                "schema": {
                    "id": {"required": True, "type": "integer"},
                    "name": {"type": "string", "nullable": False, "required": True},
                },
            },
        }
