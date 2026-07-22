# Copyright 2024 Camptocamp SA
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models
from odoo.osv import expression


class StockReleaseChannel(models.Model):
    _inherit = "stock.release.channel"

    release_channel_partner_date_ids = fields.One2many(
        comodel_name="stock.release.channel.partner.date",
        inverse_name="release_channel_id",
        string="Delivery addresses by specific date",
    )

    def action_sleep(self):
        shipment_date = self.shipment_date
        res = super().action_sleep()
        domain = self._get_release_channel_partner_date_domain(shipment_date)
        channel_dates = self.env["stock.release.channel.partner.date"].search(domain)
        channel_dates.write({"active": False})
        return res

    def _get_release_channel_partner_date_domain(self, shipment_date=None):
        domain = [("release_channel_id", "in", self.ids)]
        if shipment_date:
            domain = expression.AND(
                [
                    domain,
                    [("date", "<", shipment_date)],
                ]
            )
        return domain
