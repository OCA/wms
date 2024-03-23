# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import _

from odoo.addons.component.core import Component


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def shipment_incoming_type_only(self):
        return {
            "message_type": "error",
            "body": _("Incorrect shipment type, only incoming shipment allowed."),
        }

    def shipment_nothing_to_unload(self, shipment):
        return {
            "message_type": "warning",
            "body": _("Shipment {} has nothing to unload.").format(shipment.name),
        }

    def shipment_not_ready(self, shipment):
        return {
            "message_type": "warning",
            "body": _("Shipment {} is not ready to be worked on.").format(
                shipment.name
            ),
        }

    def shipment_not_found(self):
        return {
            "message_type": "error",
            "body": _("The shipment does not exist any more."),
        }
