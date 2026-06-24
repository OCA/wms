# Copyright 2026 ACSONE SA/NV <htts://www.acsone.eu>
# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import warnings
from collections import defaultdict
from typing import Literal

from odoo import models
from odoo.osv import expression
from odoo.tools.float_utils import float_compare


class StockMoveLine(models.Model):
    _inherit = "stock.move.line"

    def _prepare_full_location_reservation_quants_domain(
        self, package_only=None, product_only=False
    ):
        domains = []
        for line in self:
            domain = [("location_id", "=", line.location_id.id)]
            if package_only:
                if line.package_id:
                    domain += [("package_id", "=", line.package_id.id)]
                else:
                    continue
            if product_only:
                domain += [("product_id", "=", line.product_id.id)]
            domains.append(domain)
        return expression.OR(domains)

    def _get_full_location_reservation_quants(
        self, package_only=None, product_only=False
    ):
        domain = self._prepare_full_location_reservation_quants_domain(
            package_only=package_only, product_only=product_only
        )
        return self.env["stock.quant"].search(domain)

    def _get_full_location_reservable_qties(
        self, package_only=None, product_only=False
    ):
        quants = self._get_full_location_reservation_quants(
            package_only=package_only, product_only=product_only
        )
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

    def _full_location_reservation_strict(self):
        """Reserve using Odoo's _gather with strict=True (exact lot/package/owner match).

        Increments reserved_uom_qty on existing move lines - no new moves created.
        """
        Quant = self.env["stock.quant"]
        for line in self.exists():  # Move line should have been deleted
            quants = Quant._gather(
                line.product_id,
                line.location_id,
                lot_id=line.lot_id,
                package_id=line.package_id,
                owner_id=line.owner_id,
                strict=True,
            )
            if not quants:
                continue
            # We let the core mechanism occur that will reserve the needed quants
            line.reserved_uom_qty += sum(q.available_quantity for q in quants)

    def _full_location_reservation_product(self):
        """Reserve all available qty of each line's product across every package
        at the location - creates one new move per (package, product) combination.
        """
        move_ids = []
        reservable_qties = self._get_full_location_reservable_qties(product_only=True)
        for line in self.exists():
            location_qties = reservable_qties.get(line.location_id, {})
            for package in list(location_qties.keys()):
                package_qties = location_qties[package]
                qty = package_qties.pop(line.product_id, 0)
                if not package_qties:
                    location_qties.pop(package)
                if qty:
                    move_ids.append(
                        line.move_id._full_location_reservation_create_move(
                            line.product_id, qty, line.location_id, package
                        ).id
                    )
        return move_ids

    def _full_location_reservation_by_location(self, package_only=False):
        """Shared implementation: creates one new move per (location, package, product)
        combination found in reservable quantities.
        """
        move_ids = []
        reservable_qties = self._get_full_location_reservable_qties(
            package_only=package_only
        )
        for line in self.exists():
            location = line.location_id
            package = line.package_id
            qties = reservable_qties.get(location, {}).get(package, {})
            if not qties:
                continue
            for product, qty in qties.items():
                move_ids.append(
                    line.move_id._full_location_reservation_create_move(
                        product, qty, location, package
                    ).id
                )
            reservable_qties[location].pop(package)
        return move_ids

    def _full_location_reservation_package(self):
        """Reserve all products at each line's (location, package),
        skipping lines that have no package.
        """
        return self._full_location_reservation_by_location(package_only=True)

    def _full_location_reservation_default(self):
        """Reserve all products at each line's (location, package)."""
        return self._full_location_reservation_by_location()

    def _full_location_reservation(
        self,
        reservation_mode: Literal["strict", "package", "product"] | None = None,
        **kwargs,
    ):
        if "package_only" in kwargs:
            warnings.warn(
                "The 'package_only' parameter is deprecated. "
                "Use reservation_mode='package' instead.",
                DeprecationWarning,
                stacklevel=2,
            )
            if kwargs.pop("package_only"):
                reservation_mode = "package"
        if reservation_mode == "strict":
            self._full_location_reservation_strict()
            return self.env["stock.move"]
        elif reservation_mode == "product":
            move_ids = self._full_location_reservation_product()
        elif reservation_mode == "package":
            move_ids = self._full_location_reservation_package()
        else:
            move_ids = self._full_location_reservation_default()
        moves_to_assign = self.env["stock.move"].browse(move_ids)
        if moves_to_assign:
            moves_to_assign._action_confirm()
            moves_to_assign._action_assign()
        return moves_to_assign
