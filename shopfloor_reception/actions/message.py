# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def lot_already_exists_different_expiration_date(self, lot):
        formatted_lot_expiration_date = self.work.env[
            "ir.qweb.field.date"
        ].value_to_html(lot.expiration_date, {})
        return {
            "message_type": "error",
            "body": _(
                "This lot already exists with expiration date "
                "'%(lot_expiration_date)s'. You cannot change its date.",
                lot_expiration_date=formatted_lot_expiration_date,
            ),
        }

    def lot_creation_disabled(self, picking_type):
        return {
            "message_type": "error",
            "body": _(
                "The operation type '%(picking_type)s' does not allow to create new lots.",
                picking_type=picking_type.display_name,
            ),
        }

    def invalid_quantity(self, qty):
        return {
            "message_type": "error",
            "body": _(
                "Invalid quantity: '%(qty)s'.",
                qty=qty,
            ),
        }
