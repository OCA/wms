# Copyright 2026 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def new_packaging_created(self, packaging):
        return {
            "message_type": "success",
            "body": _("Packaging '{}' created.").format(packaging.name),
        }
