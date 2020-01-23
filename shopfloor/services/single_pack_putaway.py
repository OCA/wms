from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackPutaway(Component):
    """Methods for the Single Pack Put-Away Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.putaway"
    _usage = "single_pack_putaway"
    _description = __doc__

    def scan(self, barcode):
        """Scan a pack barcode"""

        company = self.env.user.company_id  # FIXME add logic to get proper company
        # FIXME add logic to get proper warehouse
        warehouse = self.env["stock.warehouse"].search([])[0]
        picking_type = (
            warehouse.int_type_id
        )  # FIXME add logic to get picking type properly

        # TODO define on what we search (pack name, pack barcode ...)
        pack = self.env["stock.quant.package"].search([("name", "=", barcode)])
        if not pack:
            return self._response(
                state="start",
                message={
                    "message_type": "error",
                    "title": _("Pack not found"),
                    "message": _("The pack %s doesn't exist") % barcode,
                },
            )
        allowed_locations = self.env["stock.location"].search(
            [("id", "child_of", picking_type.default_location_src_id.id)]
        )
        if pack.location_id not in allowed_locations:
            return self._response(
                state="start",
                message={
                    "message_type": "error",
                    "title": _("Cannot proceed"),
                    "message": _("pack %s is not in %s location")
                    % (barcode, picking_type.default_location_src_id.name),
                },
            )
        quantity = pack.quant_ids[0].quantity
        existing_operations = self.env["stock.move.line"].search(
            [("qty_done", "=", quantity), ("package_id", "=", pack.id)]
        )
        if (
            existing_operations
            and existing_operations[0].picking_id.picking_type_id != picking_type
        ):
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
        elif existing_operations:
            move = existing_operations.move_id
            return self._response(
                data={
                    "id": move.move_line_ids[0].package_level_id.id,
                    "location_src": {
                        "id": pack.location_id.id,
                        "name": pack.location_id.name,
                    },
                    "location_dst": {
                        "id": move.move_line_ids[0].location_dest_id.id,
                        "name": move.move_line_ids[0].location_dest_id.name,
                    },
                    "product": {
                        "id": move.product_id.name,
                        "name": move.product_id.name,
                    },
                    "picking": {"id": move.picking_id.id, "name": move.picking_id.name},
                },
                state="confirm_start",
                message={
                    "message_type": "warning",
                    "title": _("Already started"),
                    "message": _(
                        "Operation already running. " "Would you like to take it over ?"
                    ),
                },
            )
        product = pack.quant_ids[
            0
        ].product_id  # FIXME we consider only one product per pack
        default_location_dest = picking_type.default_location_dest_id
        move_vals = {
            "picking_type_id": picking_type.id,
            "product_id": product.id,
            "location_id": pack.location_id.id,
            "location_dest_id": default_location_dest.id,
            "name": product.name,
            "product_uom": product.uom_id.id,
            "product_uom_qty": pack.quant_ids[0].quantity,
            "company_id": company.id,
        }
        move = self.env["stock.move"].create(move_vals)
        move._action_confirm(merge=False)
        location_dest_id = (
            default_location_dest._get_putaway_strategy(product).id
            or default_location_dest.id
        )
        self.env["stock.package_level"].create(
            {
                "package_id": pack.id,
                "move_ids": [(4, move.id)],
                "company_id": company.id,
                "is_done": True,
                "location_id": pack.location_id.id,
                "location_dest_id": location_dest_id,
            }
        )
        move.picking_id.action_assign()
        return self._response(
            state="scan_location",
            message={
                "message_type": "info",
                "title": _("Start"),
                "message": _(
                    "The move is ready, you can scan the destination location."
                ),
            },
            data={
                "id": move.move_line_ids[0].package_level_id.id,
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

    def validate(self, package_level_id, location_barcode, confirmation=False):
        """Validate the transfer"""
        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response(
                state="start",
                message={
                    "message_type": "error",
                    "title": _("Start again"),
                    "message": _("This operation does not exist anymore."),
                },
            )
        move = package.move_line_ids[0].move_id
        if move.state == "cancel":
            return self._response(
                state="start",
                message={
                    "message_type": "warning",
                    "title": _("Restart"),
                    "message": _("Restart the operation, someone has canceled it."),
                },
            )
        dest_location = self.env["stock.location"].search(
            [("barcode", "=", location_barcode)]
        )
        move_dest_location = move.move_line_ids[0].location_dest_id
        allowed_locations = self.env["stock.location"].search(
            [
                (
                    "id",
                    "child_of",
                    move.picking_id.picking_type_id.default_location_dest_id.id,
                )
            ]
        )
        zone_locations = self.env["stock.location"].search(
            [("id", "child_of", move_dest_location.id)]
        )
        if dest_location not in allowed_locations:
            return self._response(
                state="scan_location",
                message={
                    "message_type": "error",
                    "title": _("Forbidden"),
                    "message": _("You cannot place it here"),
                },
            )
        elif dest_location in allowed_locations and dest_location not in zone_locations:
            if confirmation:
                move.location_dest_id = dest_location.id
            else:
                return self._response(
                    state="confirm_location",
                    message={
                        "message_type": "warning",
                        "title": _("Confirm"),
                        "message": _("Are you sure?"),
                    },
                )
        move.move_line_ids[0].location_dest_id = dest_location.id
        move._action_done()
        return self._response(
            state="start",
            message={
                "message_type": "info",
                "title": _("Start"),
                "message": _("The pack has been moved, you can scan a new pack."),
            },
        )

    def cancel(self, package_level_id):
        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response(
                state="start",
                message={
                    "message_type": "error",
                    "title": _("Start again"),
                    "message": _("This operation does not exist anymore."),
                },
            )
        package.move_ids[0].cancel()
        return self._response(
            state="start",
            message={
                "message_type": "info",
                "title": _("Start"),
                "message": _("The move has been canceled, you can scan a new pack."),
            },
        )

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

    def _validator_scan(self):
        return {"barcode": {"type": "string", "nullable": False, "required": True}}

    def _validator_return_scan(self):
        return self._response_schema(
            {
                "id": {"coerce": to_int, "required": True, "type": "integer"},
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
