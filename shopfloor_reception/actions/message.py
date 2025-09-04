# Copyright 2025 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def expiration_date_different_than_scanned(
        self, scanned_expiration_date, expiration_date
    ):
        return {
            "message_type": "error",
            "body": _(
                "The expiration date found into the scanned barcode (%(scanned)s) "
                "is different from the one explicitely provided (%(provided)s).",
                scanned=scanned_expiration_date,
                provided=expiration_date,
            ),
        }

    def lot_already_exists_different_expiration_date(self, lot, expiration_date):
        formatted_lot_expiration_date = self.work.env[
            "ir.qweb.field.date"
        ].value_to_html(lot.expiration_date, {})
        formatted_provided_expiration_date = self.work.env[
            "ir.qweb.field.date"
        ].value_to_html(expiration_date, {})
        return {
            "message_type": "error",
            "body": _(
                "A lot already exists with a different expiration date. "
                "Lot: %(lot_name)s: current expiration date: %(current)s "
                "!= provided expiration date: %(provided)s",
                lot_name=lot.name,
                current=formatted_lot_expiration_date,
                provided=formatted_provided_expiration_date,
            ),
        }
