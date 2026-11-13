# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    def _prepare_reserve_procurements(self, group):
        """express the forced blanket quantity in the procurement unit"""
        procurements = super()._prepare_reserve_procurements(group)
        forced_qty = self.env.context.get("force_qty")
        if forced_qty and self.order_type == "blanket":
            procurements = [
                procurement._replace(
                    product_qty=self.product_uom._compute_quantity(
                        forced_qty,
                        procurement.product_uom,
                        rounding_method="HALF-UP",
                    )
                )
                for procurement in procurements
            ]
        return procurements

    @api.depends(
        "order_type",
        "call_off_remaining_qty",
        "move_ids.used_for_sale_reservation",
    )
    def _compute_availability_status(self):
        # if the line is a call-off line, we need to take the availability
        # data from the blanket line, if any otherwise we take the call-off
        # line itself (This should not happen, but it's defensive programming
        # and will avoid to duplicate the logic of assigning the default value
        # for availability data into this method)
        self_call_off_lines = self.filtered(lambda line: line.order_type == "call_off")
        processed_lines = self.browse()
        if self_call_off_lines:
            matching_dict = (
                self_call_off_lines._get_blanket_lines_for_call_off_lines_dict(
                    validate=False
                )
            )
            for call_off_lines, blanket_lines in matching_dict.values():
                for call_off_line in call_off_lines:
                    if call_off_line not in processed_lines:
                        data_line = (
                            call_off_line.blanket_line_id
                            or fields.first(blanket_lines)
                            or call_off_line
                        )
                        call_off_line.update(data_line._get_availability_data())
                        processed_lines |= call_off_line
        other_lines = self - processed_lines
        return (
            super(SaleOrderLine, other_lines)._compute_availability_status()
            if other_lines
            else None
        )

    def _get_availability_required_qty(self):
        if self.order_type == "blanket":
            return max(self.call_off_remaining_qty, 0.0)
        return super()._get_availability_required_qty()

    def _get_availability_moves(self):
        moves = super()._get_availability_moves()
        if self.order_type == "blanket":
            return moves.filtered(
                lambda move: move.used_for_sale_reservation
                and move.state not in ("draft", "done")
            )
        return moves

    def _get_available_qty(self):
        if self.order_type == "blanket" and self.product_id.type in (
            "service",
            "consu",
        ):
            return self._get_availability_required_qty()
        return super()._get_available_qty()

    def _get_availability_move_qty(self, move):
        """prebook moves promise stock without physically reserving it"""
        if move.used_for_sale_reservation:
            return move.ordered_available_to_promise_uom_qty
        return super()._get_availability_move_qty(move)

    def _get_availability_data(self):
        data = super()._get_availability_data()
        if self.order_type == "blanket" and not self.display_type and self.product_id:
            remaining_qty = self._get_availability_required_qty()
            data["available_qty"] = max(min(data["available_qty"], remaining_qty), 0.0)
            data["delayed_qty"] = remaining_qty - data["available_qty"]
        return data
