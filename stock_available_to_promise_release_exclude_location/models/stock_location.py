# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models
from odoo.osv import expression


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _get_available_to_promise_domain(self):
        domain = super()._get_available_to_promise_domain()
        domain = expression.AND(
            [domain, [("location_id.exclude_from_immediately_usable_qty", "=", False)]]
        )
        return domain
