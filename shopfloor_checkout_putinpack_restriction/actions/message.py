# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def package_not_allowed_for_operation(self):
        return {
            "message_type": "error",
            "body": _("The operation does not allow the use of package"),
        }
