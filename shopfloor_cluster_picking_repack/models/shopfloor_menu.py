# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    pack_pickings = fields.Boolean(
        string="Pack pickings",
        default=False,
        help="If you tick this box, all the picked item will be put in pack"
        " before the transfer.",
    )

    default_pack_pickings_action = fields.Selection(
        [
            ("nbr_packages", "Enter the number of packages"),
            ("package_type", "Scan the package type"),
        ],
        default="nbr_packages",
    )
