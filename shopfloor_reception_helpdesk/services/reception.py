# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.stock.models.stock_move_line import StockMoveLine
from odoo.addons.stock.models.stock_picking import Picking


class Reception(Component):

    _inherit = "shopfloor.reception"

    def start_helpdesk(self, picking_id: int, selected_line_id: int):
        """
        Endpoint to start to fill in Helpdesk details
        """
        picking = self.env["stock.picking"].browse(picking_id).exists()
        line = self.env["stock.move.line"].browse(selected_line_id).exists()
        return self._response(
            next_state="start_helpdesk",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
            },
        )

    def create_helpdesk(self, picking_id: int, selected_line_id: int, description: str):
        """
        Endpoint to create the hdelpdesk ticket
        """
        picking = self.env["stock.picking"].browse(picking_id).exists()
        line = self.env["stock.move.line"].browse(selected_line_id).exists()
        ticket = self._create_helpdesk(picking, line, description)
        message = {}
        if ticket:
            message = self.msg_store.helpdesk_ticket_created(ticket)
        return self._response(
            next_state="set_destination",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
            },
            message=message,
        )

    def _prepare_ticket_wizard_values(
        self, picking: Picking, line: StockMoveLine, description: str, **kwargs
    ):
        return {"description": description}

    def _create_helpdesk(
        self, picking: Picking, line: StockMoveLine, description: str, **kwargs
    ):
        wizard = (
            self.env["stock.helpdesk.ticket.create"]
            .with_context(active_model="stock.move", active_id=line.move_id.id)
            .create(
                self._prepare_ticket_wizard_values(
                    picking, line, description=description, **kwargs
                )
            )
        )
        tickets_before = line.move_id.helpdesk_ticket_ids
        wizard.create_helpdesk_ticket()
        ticket = line.move_id.helpdesk_ticket_ids - tickets_before
        return ticket


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def start_helpdesk(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
        }

    def create_helpdesk(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "description": {"type": "string", "required": True},
        }


class ShopfloorReceptionValidatorResponse(Component):
    _inherit = "shopfloor.reception.validator.response"

    def _states(self):
        states = super()._states()
        states.update(
            {
                "start_helpdesk": self._schema_start_helpdesk,
                "create_helpdesk": self._schema_create_helpdesk,
            }
        )
        return states

    @property
    def _schema_start_helpdesk(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    @property
    def _schema_create_helpdesk(self):
        return {
            "selected_move_line": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.move_line()},
            },
            "picking": {"type": "dict", "schema": self.schemas.picking()},
        }

    def _create_helpdesk_next_states(self):
        return {"set_destination", "select_move"}

    def _start_helpdesk_next_states(self):
        return {"start_helpdesk"}

    def start_helpdesk(self):
        return self._response_schema(next_states=self._start_helpdesk_next_states())

    def create_helpdesk(self):
        return self._response_schema(next_states=self._create_helpdesk_next_states())
