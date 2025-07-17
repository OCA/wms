# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def print_job_sent(self):
        return {"message_type": "success", "body": _("Print job sent")}

    def print_error(self):
        return {"message_type": "warning", "body": _("Printing error")}
