import logging

from odoo import _

from odoo.addons.component.core import Component

_logger = logging.getLogger(__name__)


class MessageAction(Component):
    _inherit = "shopfloor.message.action"

    def report_model_unsupported(self, report):
        return {
            "message_type": "error",
            "body": _(
                "The report model '%(model)s' is not supported in this scenario.",
                model=report.model,
            ),
        }

    def lot_report_but_no_lot_defined(self):
        return {
            "message_type": "error",
            "body": _(
                "You tried to print a 'lot' report but there is no lot defined "
                "on the selected line.",
            ),
        }
