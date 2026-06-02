# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def dock_no_assigned_picking(self, dock):
        return {
            "message_type": "error",
            "body": _(
                "No assigned transfers found for Dock: '%(dock_name)s'",
                dock_name=dock.name,
            ),
        }

    def dock_pickings_filtered(self, dock):
        return {
            "message_type": "info",
            "body": _(
                "Transfers filtered by Dock: '%(dock_name)s'",
                dock_name=dock.name,
            ),
        }
