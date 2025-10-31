# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def helpdesk_ticket_created(self, ticket):
        return {
            "message_type": "success",
            "body": _(
                "Helpdesk ticket (%(ticket_name)s) created!",
                ticket_name=ticket.display_name,
            ),
        }
