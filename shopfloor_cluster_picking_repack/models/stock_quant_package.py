# Copyright 2023 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class StockQuantPackage(models.Model):
    _inherit = "stock.quant.package"

    def _sync_package_type_from_single_product(self, product, quantity):
        return super(
            StockQuantPackage, self.filtered(lambda p: not p.number_of_parcels)
        )._sync_package_type_from_single_product(product, quantity)
