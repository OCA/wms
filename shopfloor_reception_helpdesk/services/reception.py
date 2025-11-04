# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.base_rest.components.service import to_int
from odoo.addons.component.core import Component
from odoo.addons.helpdesk_mgmt_stock.wizards.stock_helpdesk_ticket_create import (
    StockHelpdeskTicketCreate,
)
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
        # Create wizard in order to keep information through screens
        wizard = self._create_helpdesk_wizard(picking, line)
        return self._response(
            next_state="start_helpdesk",
            data={
                "selected_move_line": self._data_for_move_lines(line),
                "picking": self.data.picking(picking),
                "helpdesk_wizard": self.data.helpdesk_wizard(wizard),
                "available_motives": self._get_available_motives(picking),
            },
        )

    def create_helpdesk(
        self,
        picking_id: int,
        selected_line_id: int,
        helpdesk_wizard_id: int,
        description: str,
        motive_id: int,
    ):
        """
        Endpoint to create the helpdesk ticket
        """
        picking = self.env["stock.picking"].browse(picking_id).exists()
        line = self.env["stock.move.line"].browse(selected_line_id).exists()
        wizard = (
            self.env["stock.helpdesk.ticket.create"].browse(helpdesk_wizard_id).exists()
        )
        wizard.description = description
        wizard.motive_id = motive_id

        ticket = self._create_helpdesk(picking, line, wizard)
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

    def _prepare_ticket_wizard_values(self, picking: Picking, line: StockMoveLine):
        return {}

    def _create_helpdesk_wizard(self, picking: Picking, line: StockMoveLine):
        wizard = (
            self.env["stock.helpdesk.ticket.create"]
            .with_context(active_model="stock.move", active_id=line.move_id.id)
            .create(self._prepare_ticket_wizard_values(picking, line))
        )
        return wizard

    def _create_helpdesk(
        self,
        picking: Picking,
        line: StockMoveLine,
        wizard: StockHelpdeskTicketCreate,
        **kwargs,
    ):
        tickets_before = line.move_id.helpdesk_ticket_ids
        wizard.create_helpdesk_ticket()
        ticket = line.move_id.helpdesk_ticket_ids - tickets_before
        return ticket

    def _get_available_motives(self, picking: Picking) -> list[dict]:
        domain = []
        if default_helpdesk_team := picking.picking_type_id.default_helpdesk_team_id:
            domain.append(("team_id", "=", default_helpdesk_team.id))
        return self.env["helpdesk.ticket.motive"].search_read(domain, ["id", "name"])


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
            "helpdesk_wizard_id": {
                "coerce": to_int,
                "type": "integer",
                "required": True,
            },
            "description": {"type": "string", "required": True},
            "motive_id": {"coerce": to_int, "type": "integer", "required": False},
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
            "helpdesk_wizard": {
                "type": "dict",
                "schema": self.schemas.helpdesk_wizard(),
            },
            "available_motives": {
                "type": "list",
                "schema": {"type": "dict", "schema": self.schemas.helpdesk_motive()},
            },
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
