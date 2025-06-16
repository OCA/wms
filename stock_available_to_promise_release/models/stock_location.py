# Copyright 2023 ACSONE SA/NV
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import models


class StockLocation(models.Model):
    _inherit = "stock.location"

    def _get_available_to_promise_domain(self):
        return [("location_id", "child_of", self.ids)]
