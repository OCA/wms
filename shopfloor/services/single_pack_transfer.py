from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackTransfer(Component):
    """Methods for the Single Pack Transfer Process"""

    _inherit = "base.shopfloor.process"
    _name = "shopfloor.single.pack.transfer"
    _usage = "single_pack_transfer"
    _description = __doc__

    def _data_after_package_scanned(self, package_level):
        move_line = package_level.move_line_ids[0]
        package = package_level.package_id
        # TODO use data.package_level (but the "name" moves in "package.name")
        return {
            "id": package_level.id,
            "name": package.name,
            "location_src": self.data.location(move_line.location_id),
            "location_dest": self.data.location(package_level.location_dest_id),
            "product": self.data.product(move_line.product_id),
            "picking": self.data.picking(move_line.picking_id),
        }

    def _response_for_start(self, message=None, popup=None):
        return self._response(next_state="start", message=message, popup=popup)

    def _response_for_confirm_start(self, package_level, message=None):
        data = self._data_after_package_scanned(package_level)
        data["confirmation_required"] = True
        return self._response(next_state="start", data=data, message=message,)

    def _response_for_scan_location(
        self, package_level, message=None, confirmation_required=False
    ):
        data = self._data_after_package_scanned(package_level)
        data["confirmation_required"] = confirmation_required
        return self._response(next_state="scan_location", data=data, message=message,)

    def _response_for_show_completion_info(self, message=None):
        return self._response(next_state="show_completion_info", message=message)

    def start(self, barcode, confirmation=False):
        search = self.actions_for("search")
        picking_types = self.picking_types
        location = search.location_from_scan(barcode)

        package = self.env["stock.quant.package"]
        if location:
            package = self.env["stock.quant.package"].search(
                [("location_id", "=", location.id)]
            )
            if not package:
                return self._response_for_start(
                    message=self.msg_store.no_pack_in_location(location)
                )
            if len(package) > 1:
                return self._response_for_start(
                    message=self.msg_store.several_packs_in_location(location)
                )

        if not package:
            package = search.package_from_scan(barcode)

        if not package:
            return self._response_for_start(
                self.msg_store.package_not_found_for_barcode(barcode)
            )

        if not package.location_id.is_sublocation_of(
            picking_types.mapped("default_location_src_id")
        ):
            return self._response_for_start(
                message=self.msg_store.package_not_allowed_in_src_location(
                    barcode, picking_types
                )
            )

        package_level = self.env["stock.package_level"].search(
            [
                ("package_id", "=", package.id),
                ("picking_id.picking_type_id", "in", picking_types.ids),
            ]
        )
        # State is computed, can't use it in the domain. And it's probably faster
        # to filter here rather than using a domain on "picking_id.state" that would
        # use a sub-search on stock.picking: we shouldn't have dozens of package levels
        # for a package.
        package_level = package_level.filtered(
            lambda pl: pl.state not in ("cancel", "done")
        )
        if not package_level:
            if self.work.menu.allow_move_create:
                package_level = self._create_package_level(package)

        if not package_level:
            return self._response_for_start(
                message=self.msg_store.no_pending_operation_for_pack(package)
            )
        if package_level.is_done and not confirmation:
            return self._response_for_confirm_start(
                package_level, message=self.msg_store.already_running_ask_confirmation()
            )
        if not package_level.is_done:
            package_level.is_done = True
        return self._response_for_scan_location(package_level)

    def _create_package_level(self, package):
        # this method can be called only if we have one picking type
        # (allow_move_create==True on menu)
        assert self.picking_types.ensure_one()
        StockPicking = self.env["stock.picking"].with_context(
            default_picking_type_id=self.picking_types.id
        )
        picking = StockPicking.create({})
        package_level = self.env["stock.package_level"].create(
            {
                "picking_id": picking.id,
                "package_id": package.id,
                "location_dest_id": picking.location_dest_id.id,
                "company_id": self.env.company.id,
            }
        )
        package_level._generate_moves()
        picking.action_confirm()
        picking.action_assign()
        return package_level

    def _is_move_state_valid(self, move):
        return move.state != "cancel"

    def _is_dest_location_valid(self, move, scanned_location):
        """Forbid a dest location to be used"""
        return scanned_location.is_sublocation_of(
            move.picking_id.picking_type_id.default_location_dest_id
        )

    def _is_dest_location_to_confirm(self, move, scanned_location):
        """Destination that could be used but need confirmation"""
        move_dest_location = move.move_line_ids[0].location_dest_id
        return not scanned_location.is_sublocation_of(move_dest_location)

    def validate(self, package_level_id, location_barcode, confirmation=False):
        """Validate the transfer"""
        search = self.actions_for("search")

        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            return self._response_for_start(
                message=self.msg_store.operation_not_found()
            )

        # if we have more than one move, we should assume they go to the same
        # place
        move_line = package_level.move_line_ids[0]
        move = move_line.move_id
        if not self._is_move_state_valid(move):
            return self._response_for_start(
                message=self.msg_store.operation_has_been_canceled_elsewhere()
            )

        scanned_location = search.location_from_scan(location_barcode)
        if not scanned_location:
            return self._response_for_scan_location(
                package_level, message=self.msg_store.no_location_found()
            )

        if not self._is_dest_location_valid(move, scanned_location):
            return self._response_for_scan_location(
                package_level, message=self.msg_store.dest_location_not_allowed()
            )

        if self._is_dest_location_to_confirm(move, scanned_location):
            if confirmation:
                # If the destination of the move would be incoherent
                # (move line outside of it), we change the moves' destination
                if not scanned_location.is_sublocation_of(move.location_dest_id):
                    move.location_dest_id = scanned_location.id
            else:
                return self._response_for_scan_location(
                    package_level,
                    confirmation_required=True,
                    message=self.msg_store.confirm_location_changed(
                        move_line.location_dest_id, scanned_location
                    ),
                )

        self._set_destination_and_done(move, scanned_location)
        return self._router_validate_success(package_level)

    def _is_last_move(self, move):
        return move.picking_id.completion_info == "next_picking_ready"

    def _router_validate_success(self, package_level):
        move = package_level.move_line_ids.move_id

        message = self.msg_store.confirm_pack_moved()

        completion_info_popup = None
        if self._is_last_move(move):
            completion_info = self.actions_for("completion.info")
            completion_info_popup = completion_info.popup(package_level.move_line_ids)
        return self._response_for_start(message=message, popup=completion_info_popup)

    def _set_destination_and_done(self, move, scanned_location):
        # when writing the destination on the package level, it writes
        # on the move lines
        move.move_line_ids.package_level_id.location_dest_id = scanned_location
        move._action_done()

    def cancel(self, package_level_id):
        package_level = self.env["stock.package_level"].browse(package_level_id)
        if not package_level.exists():
            return self._response_for_start(
                message=self.msg_store.operation_not_found()
            )
        # package.move_ids may be empty, it seems
        move = package_level.move_line_ids.move_id
        if move.state == "done":
            return self._response_for_start(message=self.msg_store.already_done())

        package_level.is_done = False
        return self._response_for_start(
            message=self.msg_store.confirm_canceled_scan_next_pack()
        )


class SinglePackTransferValidator(Component):
    """Validators for Single Pack Transfer methods"""

    _inherit = "base.shopfloor.validator"
    _name = "shopfloor.single.pack.transfer.validator"
    _usage = "single_pack_transfer.validator"

    def start(self):
        return {
            "barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "boolean", "required": False},
        }

    def cancel(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"}
        }

    def validate(self):
        return {
            "package_level_id": {"coerce": to_int, "required": True, "type": "integer"},
            "location_barcode": {"type": "string", "nullable": False, "required": True},
            "confirmation": {"type": "boolean", "required": False},
        }


class SinglePackTransferValidatorResponse(Component):
    """Validators for Single Pack Transfer methods responses"""

    _inherit = "base.shopfloor.validator.response"
    _name = "shopfloor.single.pack.transfer.validator.response"
    _usage = "single_pack_transfer.validator.response"

    def _states(self):
        """List of possible next states

        With the schema of the data send to the client to transition
        to the next state.
        """
        schema_for_start = self._schema_for_package_level_details()
        schema_for_start.update(self._schema_confirmation_required())
        schema_for_scan_location = self._schema_for_package_level_details(required=True)
        schema_for_scan_location.update(self._schema_confirmation_required())
        return {
            "start": schema_for_start,
            "scan_location": schema_for_scan_location,
        }

    def start(self):
        return self._response_schema(next_states={"start", "scan_location"})

    def cancel(self):
        return self._response_schema(next_states={"start"})

    def validate(self):
        return self._response_schema(next_states={"scan_location", "start"})

    def _schema_for_package_level_details(self, required=False):
        # TODO use schemas.package_level (but the "name" moves in "package.name")
        return {
            "id": {"required": required, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": required},
            "location_src": {"type": "dict", "schema": self.schemas.location()},
            "location_dest": {"type": "dict", "schema": self.schemas.location()},
            "product": {"type": "dict", "schema": self.schemas.product()},
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    def _schema_confirmation_required(self):
        return {
            "confirmation_required": {
                "type": "boolean",
                "nullable": True,
                "required": False,
            },
        }
