# Copyright 2020 Camptocamp (https://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).

from odoo import api, fields, models


class ProcurementGroup(models.Model):
    _inherit = "procurement.group"

    date_expected = fields.Date(
        "Delivery Date", compute="_compute_date_expected", store="True"
    )

    @api.depends("sale_id")
    def _compute_date_expected(self):
        # expected_date is not stored on sale order but when we process
        # procurement group it will never changed so we can store it on this
        # level
        for group in self:
            so = group.sale_id
            if so:
                group.date_expected = so.commitment_date or so.expected_date
            else:
                group.date_expected = False
