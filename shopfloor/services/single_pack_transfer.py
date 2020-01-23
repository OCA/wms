from odoo import _

from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class SinglePackTransfer(Component):
    """Methods for the Single Pack Transfer Process"""

    _inherit = "base.shopfloor.service"
    _name = "shopfloor.single.pack.transfer"
    _usage = "single_pack_transfer"
    _description = __doc__

    def _response_for_package_not_found(self):
        return self._response(
            state="start",
            message={
                "message_type": "error",
                "title": _("Start again"),
                "message": _("This operation does not exist anymore."),
            },
        )

    def _response_for_move_canceled(self):
        return self._response(
            state="start",
            message={
                "message_type": "warning",
                "title": _("Restart"),
                "message": _("Restart the operation, someone has canceled it."),
            },
        )

    def _response_for_forbidden_location(self):
        return self._response(
            state="scan_location",
            message={
                "message_type": "error",
                "title": _("Forbidden"),
                "message": _("You cannot place it here"),
            },
        )

    def _response_for_location_need_confirm(self):
        return self._response(
            state="confirm_location",
            message={
                "message_type": "warning",
                "title": _("Confirm"),
                "message": _("Are you sure?"),
            },
        )

    def _response_for_validate_success(self):
        return self._response(
            state="start",
            message={
                "message_type": "info",
                "title": _("Start"),
                "message": _("The pack has been moved, you can scan a new pack."),
            },
        )

    def validate(self, package_level_id, location_barcode, confirmation=False):
        """Validate the transfer"""
        pack_transfer = self.actions_for("pack.transfer.validate")

        package = self.env["stock.package_level"].browse(package_level_id)
        if not package.exists():
            return self._response_for_package_not_found()

        move = package.move_line_ids[0].move_id
        if not pack_transfer.is_move_state_valid(move):
            return self._response_for_move_canceled()

        scanned_location = pack_transfer.location_from_scan(location_barcode)
        if not pack_transfer.is_dest_location_valid(move, scanned_location):
            return self._response_for_forbidden_location()

        if not pack_transfer.is_dest_location_to_confirm(move, scanned_location):
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
