# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ProductPackagingType(models.Model):
    _inherit = "product.packaging.type"

    icon = fields.Image()
