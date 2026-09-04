# Copyright 2026 Acsone SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def default_workstation_set_to(self, workstation):
        return {
            "message_type": "info",
            "body": _("Default workstation set to %s", workstation.name),
        }

    def workstation_not_found(self):
        return {
            "message_type": "error",
            "body": _("Workstation not found"),
        }
