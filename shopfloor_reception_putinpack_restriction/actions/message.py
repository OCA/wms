# Copyright 2026 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def package_not_allowed_for_operation(self, picking):
        return {
            "message_type": "error",
            "body": _(
                "The operation '%(picking_type)s' does not allow the use of package.",
                picking_type=picking.picking_type_id.display_name,
            ),
        }

    def package_required_for_operation(self, picking):
        return {
            "message_type": "error",
            "body": _(
                "The operation '%(picking_type)s' requires a package.",
                picking_type=picking.picking_type_id.display_name,
            ),
        }
