# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models
from odoo.osv import expression


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _get_available_to_promise_domain(self):
        location_domain = []
        for location in self:
            location_domain = expression.OR(
                [
                    location_domain,
                    [("location_id.parent_path", "=like", location.parent_path + "%")],
                ]
            )
        return location_domain
