# Copyright 2018 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import models


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    def action_print_cash_on_delivery_invoices(self):
        if self.shipment_advice_to_print_ids:
            return self.shipment_advice_to_print_ids.print_cash_on_delivery_invoices()
        return {}
