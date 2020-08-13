from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    shopfloor_packing_info = fields.Text(string="Checkout Packing Information")
