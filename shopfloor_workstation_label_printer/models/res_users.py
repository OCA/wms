# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from warnings import warn

from odoo import models


class ResUsers(models.Model):
    _inherit = "res.users"

    # TODO method to remove when migrating to 15.0+
    def get_delivery_label_printer(self, delivery_type):
        self.ensure_one()
        warn(
            "'res.users.get_delivery_label_printer' method is deprecated. "
            "Consider to switch to 'ir.actions.report._get_user_default_printer' "
            "from 'base_report_to_label_printer' module.",
            DeprecationWarning,
        )
        return self.default_label_printer_id
