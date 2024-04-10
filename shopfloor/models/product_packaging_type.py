# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class ProductPackagingType(models.Model):
    _inherit = "product.packaging.type"

    shopfloor_icon = fields.Binary(
        help="Icon to be displayed in the frontend qty picker. "
        "Its final size will be a 30x30 image, "
        "which means that square-shaped icons will work best."
    )
