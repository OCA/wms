# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models
from odoo.osv import expression


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _release_channel_id_domain_parts(self):
        domain = super()._release_channel_id_domain_parts()
        domain.append(
            "'|', ('carrier_ids', '=', False), ('carrier_ids', '=', carrier_id)"
        )
        return domain

    def _get_release_channel_id_depends(self):
        depends = super()._get_release_channel_id_depends()
        depends.append("carrier_id")
        return depends

    def _get_release_channel_partner_date_domain(self):
        domain = super()._get_release_channel_partner_date_domain()
        if domain:
            if self.carrier_id:
                carrier_domain = [
                    ("release_channel_id.carrier_ids", "in", self.carrier_id.ids),
                ]
            else:
                carrier_domain = [
                    ("release_channel_id.carrier_ids", "=", False),
                ]
            domain = expression.AND([domain, carrier_domain])
        return domain

    def _compute_release_channel_id(self):
        # pylint: disable=missing-return
        super()._compute_release_channel_id()
        for rec in self:
            # Selected release channel and carrier have to be compatible
            if rec.release_channel_id.carrier_ids and rec.carrier_id:
                if rec.carrier_id not in rec.release_channel_id.carrier_ids:
                    rec.release_channel_id = False
