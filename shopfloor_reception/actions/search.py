# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.component.core import Component


class SearchAction(Component):

    _inherit = "shopfloor.search.action"

    def _get_origin_from_barcode(self, barcode):
        if self.work.menu.scenario_id.key == "reception":
            carriers = self.env["delivery.carrier"].search([])
            return carriers._get_origin_from_barcode(barcode)
