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

    def start_helpdesk(self, picking_id: int, state: str, selected_line_id: int = None):
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
                "origin_state": state,
            },
        )

    def _create_helpdesk_response(self, picking, line, origin_state, message):
        if origin_state == "set_quantity":
            return self._response_for_set_destination(
                picking,
                line,
                message=message,
            )
        return self._response_for_select_move(picking, message)

    def create_helpdesk(
        self,
        picking_id: int,
        helpdesk_wizard_id: int,
        description: str,
        motive_id: int,
        origin_state: str,
        selected_line_id: int = None,
    ):
        """
        Endpoint to create the helpdesk ticket
        """
        picking = self.env["stock.picking"].browse(picking_id).exists()
        line = self.env["stock.move.line"].browse(selected_line_id).exists()

        wizard = (
            self.env["stock.helpdesk.ticket.create"].browse(helpdesk_wizard_id).exists()
        )
        wizard.write(
            {
                "description": description,
                "motive_id": motive_id,
            }
        )

        ticket = self._create_helpdesk(picking, line, wizard)
        message = {}
        if ticket:
            message = self.msg_store.helpdesk_ticket_created(ticket)
        return self._create_helpdesk_response(picking, line, origin_state, message)

    def _prepare_ticket_wizard_values(self, picking: Picking, line: StockMoveLine):
        return {"stock_picking_id": picking.id, "stock_move_id": line.move_id.id}

    def _create_helpdesk_wizard(self, picking: Picking, line: StockMoveLine):
        wizard = self.env["stock.helpdesk.ticket.create"].create(
            self._prepare_ticket_wizard_values(picking, line)
        )
        return wizard

    def _create_helpdesk(
        self,
        picking: Picking,
        line: StockMoveLine,
        wizard: StockHelpdeskTicketCreate,
        **kwargs,
    ):
        action = wizard.action_create_helpdesk_ticket()
        ticket = self.env["helpdesk.ticket"].search(action["domain"])
        return ticket

    def _get_available_motives(self, picking: Picking) -> list[dict]:
        default_helpdesk_team = picking.picking_type_id.default_helpdesk_team_id
        return self.env["helpdesk.ticket.motive"].search_read(
            [("team_id", "in", default_helpdesk_team.ids + [False])], ["id", "name"]
        )


class ShopfloorReceptionValidator(Component):
    _inherit = "shopfloor.reception.validator"

    def start_helpdesk(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "state": {"type": "string", "required": True},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": False,
                "nullable": True,
            },
        }

    def create_helpdesk(self):
        return {
            "picking_id": {"coerce": to_int, "required": True, "type": "integer"},
            "origin_state": {"type": "string", "required": True},
            "selected_line_id": {
                "coerce": to_int,
                "type": "integer",
                "required": False,
                "nullable": True,
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
            "origin_state": {"type": "string"},
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
