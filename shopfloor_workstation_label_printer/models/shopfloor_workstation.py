# Copyright 2021 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields, models


class ShopfloorWorkstation(models.Model):
    _inherit = "shopfloor.workstation"

    default_label_printer_id = fields.Many2one(
        comodel_name="printing.printer", string="Default Label Printer"
    )

    def set_as_default_on_user(self, user):
        super().set_as_default_on_user(user)
        if self.default_label_printer_id:
            user.default_label_printer_id = self.default_label_printer_id
        return
