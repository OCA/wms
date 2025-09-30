# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)


from odoo.fields import Command

from odoo.addons.component.core import Component


class Reception(Component):

    _inherit = "shopfloor.reception"

    def _data_for_backorder_reasons(self, reasons):
        return self.data.backorder_reasons(reasons)

    def _response_for_choose_backorder_reason(self, picking, message=None):

        reasons = self.env["stock.backorder.reason"].search([])
        data = {
            "picking": self._data_for_stock_picking(picking, with_lines=False),
            "backorder_reasons": [
                result for result in self._data_for_backorder_reasons(reasons)
            ],
        }
        return self._response(
            next_state="choose_backorder_reason", data=data, message=message
        )

    def done_action(self, picking_id, confirmation=False):
        """
        Override here the `done_action` to let the user decide
        about the backorder reason.
        """
        picking = self.env["stock.picking"].browse(picking_id)
        action = picking.with_context(
            button_validate_picking_ids=picking.ids
        )._pre_action_done_hook()
        if (
            isinstance(action, dict)
            and action.get("res_model") == "stock.backorder.reason.choice"
        ):
            return self._response_for_choose_backorder_reason(picking)
        if isinstance(action, bool) and action and picking.state == "done":
            return self._response_for_select_document(
                message=self.msg_store.transfer_done_success(picking)
            )
        return super().done_action(picking_id, confirmation=confirmation)

    def choose_backorder_reason(self, picking_id, reason_id):
        picking = self.env["stock.picking"].browse(picking_id)
        message = self._check_picking_processible(picking)
        if message:
            return self._response_for_select_move(picking, message=message)
        # Check if reason choice is still possible
        action = picking._pre_action_done_hook()
        if action.get("res_model") == "stock.backorder.reason.choice":
            result = (
                self.env["stock.backorder.reason.choice"]
                .with_context(button_validate_picking_ids=picking.ids)
                .new(
                    {
                        "picking_ids": [Command.set([picking_id])],
                        "choice_line_ids": [Command.create({"picking_id": picking_id})],
                        "reason_id": reason_id,
                    }
                )
                .apply()
            )
            if result:
                return self._response_for_select_document(
                    message=self.msg_store.transfer_done_success(picking)
                )
        if picking.state == "done":
            # Backorder has been transparent cancelled with no reason choice
            return self._response_for_select_document(
                message=self.msg_store.transfer_done_success(picking)
            )
        return super().done_action(picking_id, confirmation=None)


class ShopfloorReceptionValidator(Component):

    _inherit = "shopfloor.reception.validator"

    def choose_backorder_reason(self):
        return {
            "picking_id": {"required": True, "type": "integer"},
            "reason_id": {"required": True, "type": "integer"},
        }


class ShopfloorReceptionValidatorResponse(Component):

    _inherit = "shopfloor.reception.validator.response"

    # STATES

    def _states(self):
        states = super()._states()
        states.update({"choose_backorder_reason": self._schema_choose_backorder_reason})

        return states

    @property
    def _schema_choose_backorder_reason(self):
        return {
            "picking": {"type": "dict", "schema": self.schemas.picking()},
            "backorder_reasons": self.schemas._schema_list_of(
                self.schemas.backorder_reason(), required=True
            ),
        }

    def choose_backorder_reason(self):
        return self._response_schema(next_states={"confirm_done"})

    def _done_next_states(self):
        next_states = super()._done_next_states()
        next_states.update({"choose_backorder_reason"})
        return next_states


class ShopfloorSchemaAction(Component):
    _inherit = "shopfloor.schema.action"

    def backorder_reason(self):
        return {
            "id": {"required": True, "type": "integer"},
            "name": {"type": "string", "nullable": False, "required": True},
            "backorder_action_to_do": {"type": "dict"},
        }
