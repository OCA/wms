# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields, models


class FakeMeasuringDevice(models.Model):
    _inherit = "measuring.device"

    device_type = fields.Selection(selection_add=[("fake", "FAKE")])

    def mocked_measure(self, measurements):
        self.ensure_one()
        self._update_packaging_measures(measurements)
