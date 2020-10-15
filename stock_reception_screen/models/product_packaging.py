# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class ProductPackaging(models.Model):
    _inherit = "product.packaging"

    storage_type_name = fields.Char(
        related="package_storage_type_id.name", string="Storage Type"
    )
