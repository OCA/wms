# Copyright 2023 ACSONE SA/NV
# Copyright 2024 Camptocamp
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    block_release = fields.Boolean(
        default=False,
        readonly=True,
        states={"draft": [("readonly", False)]},
        help="Block the release of the generated delivery at order confirmation.",
    )
