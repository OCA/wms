# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ShopfloorMenu(models.Model):
    _inherit = "shopfloor.menu"

    label_print_report_id = fields.Many2one(
        string="Print Report for Labels",
        comodel_name="ir.actions.report",
        domain=[("label", "=", True)],
        help="Choose here the report to print. "
        "Only reports with 'label' field checked will be available.",
    )
    display_print_label_button = fields.Boolean()
