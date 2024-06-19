# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):

    _inherit = "res.company"

    stock_sale_report_display_is_available = fields.Boolean(
        help="Show Available column in SO and quotation reports",
        default=True,
    )
