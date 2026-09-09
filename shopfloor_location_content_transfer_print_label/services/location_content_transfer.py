# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class LocationContentTransfer(Component):
    _inherit = "shopfloor.location.content.transfer"

    def print_labels(
        self,
        move_line_ids,
        quantity,
    ) -> dict:
        """
        Print labels using the printing component.
        The report is defined on menu level.
        """
        move_lines = self.env["stock.move.line"].browse(move_line_ids)
        picking = move_lines.picking_id

        printing = self._printing_for("location_content_transfer")
        result = printing.print(record_ids=move_lines.ids, quantity=quantity)
        if result:
            message = self.msg_store.print_job_sent()
        else:
            message = self.msg_store.print_error()
        return self._response_for_scan_destination_all(picking, message=message)


class ShopfloorLocationContentTransferValidator(Component):
    _inherit = "shopfloor.location.content.transfer.validator"

    def print_labels(self) -> dict:
        return {
            "move_line_ids": {
                "type": "list",
                "required": True,
                "schema": {
                    "coerce": to_int,
                    "type": "integer",
                },
            },
            "quantity": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }


class ShopfloorLocationContentTransferValidatorResponse(Component):
    _inherit = "shopfloor.location.content.transfer.validator.response"

    def print_labels(self) -> dict:
        return self._response_schema(next_states={"scan_destination_all"})
