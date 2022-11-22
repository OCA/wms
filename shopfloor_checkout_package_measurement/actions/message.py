# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def package_measurement_changed(self):
        return {
            "message_type": "success",
            "body": _("Package measure(s) changed."),
        }
