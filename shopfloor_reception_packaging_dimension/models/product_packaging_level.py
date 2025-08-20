# Copyright 2025 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from odoo import fields, models

HELP_TEXT = (
    "When marked, shopfloor will require to set this dimension during "
    "reception if undefined on the packaging"
)


class ProductPackagingLevel(models.Model):
    _inherit = "product.packaging.level"

    shopfloor_collect_length = fields.Boolean(
        "Collect length",
        default=True,
        help=HELP_TEXT,
    )
    shopfloor_collect_width = fields.Boolean(
        "Collect width",
        default=True,
        help=HELP_TEXT,
    )
    shopfloor_collect_height = fields.Boolean(
        "Collect height",
        default=True,
        help=HELP_TEXT,
    )
    shopfloor_collect_weight = fields.Boolean(
        "Collect weight",
        default=True,
        help=HELP_TEXT,
    )
