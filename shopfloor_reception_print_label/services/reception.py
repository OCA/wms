# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component


class Reception(Component):
    _inherit = "shopfloor.reception"

    def print_labels(
        self,
        picking_id,
        selected_line_id,
        quantity,
    ) -> dict:
        """
        Print labels using the printing component.
        The report is defined on menu level.
        """
        picking = self.env["stock.picking"].browse(picking_id)
        selected_line = self.env["stock.move.line"].browse(selected_line_id)

        printing = self._printing_for("reception")
        report = printing.report_to_print

        if not report:
            return printing.msg_store.print_no_report()

        # Dynamically resolve record_ids based on the target report model
        if report.model == "stock.move.line":
            record_ids = selected_line.ids
        elif report.model == "stock.lot":
            if not selected_line.lot_id:
                return self._response_for_set_destination(
                    picking,
                    selected_line,
                    message=self.msg_store.lot_report_but_no_lot_defined(),
                )
            record_ids = selected_line.lot_id.ids
        elif report.model == "stock.picking":
            record_ids = picking.ids
        elif report.model == "product.product":
            record_ids = selected_line.product_id.ids
        elif report.model == "product.template":
            record_ids = selected_line.product_id.product_tmpl_id.ids

        else:
            return self._response_for_set_destination(
                picking,
                selected_line,
                message=self.msg_store.report_model_unsupported(report),
            )

        message = printing.print(record_ids=record_ids, quantity=quantity)
        return self._response_for_set_destination(
            picking, selected_line, message=message
        )


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def print_labels(self) -> dict:
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
            "quantity": {
                "coerce": to_int,
                "required": True,
                "type": "integer",
            },
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self) -> dict:
        res = super()._states()
        res.update(
            {
                "print_labels": self._schema_set_destination,
            }
        )
        return res
