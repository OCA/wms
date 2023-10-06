# Copyright 2023 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockPicking(models.Model):

    _inherit = "stock.picking"

    def _get_release_channel_possible_candidate_domain(self):
        """
        override to exclude deliveries (OUT pickings) where
        the date_deadline is after the shipment date.
        """
        self.ensure_one()
        domain = super()._get_release_channel_possible_candidate_domain()

        # date_deadline is datetime UTC => convert to timezone user to compare
        # with shipment_date is date
        if self.date_deadline:
            date_deadline = fields.Datetime.context_timestamp(
                self, self.date_deadline
            ).date()

            domain.extend(
                [
                    "|",
                    ("shipment_date", "=", False),
                    ("shipment_date", ">=", date_deadline),
                ]
            )
        return domain
