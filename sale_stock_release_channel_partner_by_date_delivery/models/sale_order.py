# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import models


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
