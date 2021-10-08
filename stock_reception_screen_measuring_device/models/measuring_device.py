# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class MeasuringDevice(models.Model):
    _inherit = "measuring.device"

    is_default = fields.Boolean(
        "Default",
        default=False,
        help="The device set as the default one will be "
        "the one used in the reception screen.",
    )

    @api.constrains("is_default")
    def _check_is_default(self):
        self.ensure_one()
        if self.search_count([("is_default", "=", True)]) > 1:
            raise ValidationError(
                _("Only one measuring device can be the default one.")
            )
