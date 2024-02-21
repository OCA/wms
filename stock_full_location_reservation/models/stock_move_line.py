# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from collections import defaultdict

from odoo import models
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _prepare_full_location_reservation_quants_domain(self, package_only=None):
        domains = []
        for line in self:
            domain = [("location_id", "=", line.location_id.id)]
            if package_only:
                if line.package_id:
                    domain += [("package_id", "=", line.package_id.id)]
                else:
                    continue
            domains.append(domain)
        return expression.OR(domains)

    def _get_full_location_reservation_quants(self, package_only=None):
        domain = self._prepare_full_location_reservation_quants_domain(package_only)
        return self.env["stock.quant"].search(domain)

    def _get_full_location_reservable_qties(self, package_only=None):
        quants = self._get_full_location_reservation_quants(package_only)
        res = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: 0)))
        for quant in quants:
            qty_available = quant.available_quantity
            if (
                float_compare(
                    qty_available, 0, precision_rounding=quant.product_uom_id.rounding
                )
                > 0
            ):
                res[quant.location_id][quant.package_id][
                    quant.product_id
                ] += qty_available
        return res

    def _full_location_reservation(self, package_only=None):
        reservable_qties = self._get_full_location_reservable_qties(package_only)
        moves_to_assign_ids = []
        for line in self.exists():  # Move line should have been deleted
            # Copy location and package as move line could be deleted if merge occurs
            location = line.location_id
            package = line.package_id
            qties = reservable_qties.get(location, {}).get(package, {})
            if not qties:
                continue
            for product, qty in qties.items():
                moves_to_assign_ids.append(
                    line.move_id._full_location_reservation_create_move(
                        product, qty, location, package
                    ).id
                )
            reservable_qties[location].pop(package)
        moves_to_assign = self.env["stock.move"].browse(moves_to_assign_ids)
        if moves_to_assign:
            moves_to_assign._action_confirm()
            moves_to_assign._action_assign()
        return moves_to_assign
