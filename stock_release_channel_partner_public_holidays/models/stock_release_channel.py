# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockReleaseChannel(models.Model):

    _inherit = "stock.release.channel"

    exclude_public_holidays = fields.Boolean()
