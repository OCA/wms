# Copyright 2026 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def no_picking_found_for_grn(self, grn):
        return {
            "message_type": "info",
            "body": _(
                "No transfer found for GRN '%(grn_name)s' ",
                grn_name=grn.name,
            ),
        }

    def grn_pickings_filtered(self, grn):
        return {
            "message_type": "success",
            "body": _(
                "Transfers filtered by GRN: '%(grn_name)s'",
                grn_name=grn.name,
            ),
        }
