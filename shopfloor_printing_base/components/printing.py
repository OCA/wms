# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.component.components.base import AbstractComponent


class ShopFloorPrintingAction(AbstractComponent):
    """Base Component for actions"""

    _name = "shopfloor.printing.action"
    _inherit = "shopfloor.process.action"
    _collection = "shopfloor.printing"

    @property
    def report_to_print(self):
        """
        Returns the report to print
        """
        return self.work.menu.label_print_report_id

    def print(self, record_ids, quantity=1, **kwargs):
        """
        Print the current report defined on menu level with the
        defined quantity.
        """
        report = self.report_to_print
        result = report.print_document_client_action(
            record_ids, **{"quantity": quantity}
        )
        return result
