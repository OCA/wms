# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo import api, fields, models


class ResUsers(models.Model):
    _inherit = "res.users"

    default_label_printer_id = fields.Many2one(
        comodel_name="printing.printer", string="Default Label Printer"
    )

    @api.model
    def _register_hook(self):
        super()._register_hook()
        self.SELF_WRITEABLE_FIELDS.extend(["default_label_printer_id"])
        self.SELF_READABLE_FIELDS.extend(["default_label_printer_id"])

    def get_delivery_label_printer(self, delivery_type):
        self.ensure_one()
        return self.default_label_printer_id
