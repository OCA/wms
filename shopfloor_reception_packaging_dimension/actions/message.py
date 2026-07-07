import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def packaging_updated(self, packaging):
        return {
            "message_type": "success",
            "body": _("Packaging '{}' updated.").format(packaging.name),
        }

    def new_packaging_created(self, packaging):
        return {
            "message_type": "success",
            "body": _("Packaging '{}' created.").format(packaging.name),
        }

    def packaging_deleted(self, packaging):
        return {
            "message_type": "success",
            "body": _("Packaging '{}' deleted.").format(packaging.name),
        }
