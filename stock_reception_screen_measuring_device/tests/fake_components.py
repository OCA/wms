# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class FakeDevice(Component):
    _name = "device.component.fake"
    _inherit = "measuring.device.base"
    _usage = "fake"

    def post_update_packaging_measures(self, measures, packaging, wizard_line):
        # Unassign measuring device when measuring is done
        packaging._measuring_device_release()
