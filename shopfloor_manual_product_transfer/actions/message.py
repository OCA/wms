# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def qty_exceeds_initial_qty(self):
        return {
            "message_type": "error",
            "body": _("This quantity exceeds the initial one."),
        }
