# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.components.base import AbstractComponent
from odoo.addons.shopfloor_base.actions.base_action import get_actions_for


class ShopFloorPrintingAction(AbstractComponent):
    """Base Component for actions"""

    _name = "shopfloor.printing.action"
    _inherit = "shopfloor.process.action"
    _collection = "shopfloor.printing"

    @property
    def msg_store(self):
        return get_actions_for(self, "message")

    @property
    def report_to_print(self):
        """
        Returns the report to print
        """
        return self.work.menu.label_print_report_id.sudo()

    def print(self, record_ids, quantity=1, **kwargs) -> dict:
        """
        Print the current report defined on menu level with the
        defined quantity.

        return: A message dictionary
        """
        report = self.report_to_print
        message = dict()
        if not report:
            message = self.msg_store.print_no_report()
            return message
        result = report.print_document_client_action(
            record_ids, **{"quantity": quantity}
        )
        if result:
            message = self.msg_store.print_job_sent()
        else:
            message = self.msg_store.print_error()
        return message
