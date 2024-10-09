# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    is_full_location_reservation = fields.Boolean(
        "Full location reservation move", default=False
    )

    def _filter_full_location_reservation_moves(self):
        return self.filtered(lambda m: m.is_full_location_reservation)

    def _do_unreserve(self):
        if self.env.context.get("skip_undo_full_location_reservation"):
            return super()._do_unreserve()
        full_location_moves = self._filter_full_location_reservation_moves()
        full_location_moves._undo_full_location_reservation()
        return super(StockMove, (self - full_location_moves))._do_unreserve()

    def undo_full_location_reservation(self):
        full_location_moves = self._filter_full_location_reservation_moves()
        full_location_moves._undo_full_location_reservation()

    def _undo_full_location_reservation(self):
        if not self.exists():
            return
        self = self.with_context(skip_undo_full_location_reservation=True)
        self._do_unreserve()
        self._action_cancel()
        self.unlink()

    def _prepare_full_location_reservation_package_level_vals(self, package):
        return {
            "package_id": package.id,
            "company_id": self.company_id.id,
        }

    def _full_location_reservation_create_package_level(self, package):
        return self.env["stock.package_level"].create(
            self._prepare_full_location_reservation_package_level_vals(package)
        )

    def _full_location_reservation_prepare_move_vals(
        self, product, qty, location, package=None
    ):
        self.ensure_one()
        package_level_id = False
        if package:
            package_level_id = self._full_location_reservation_create_package_level(
                package
            ).id
        return {
            "is_full_location_reservation": True,
            "product_uom_qty": qty,
            "name": product.name,
            "product_uom": product.uom_id.id,
            "product_id": product.id,
            "location_id": location.id,
            "location_dest_id": self.picking_id.location_dest_id.id,
            "picking_id": self.picking_id.id,
            "package_level_id": package_level_id,
        }

    def _full_location_reservation_create_move(
        self, product, qty, location, package=None
    ):
        return self.create(
            self._full_location_reservation_prepare_move_vals(
                product, qty, location, package
            )
        )

    def _full_location_reservation(self, package_only=None):
        return self.move_line_ids._full_location_reservation(package_only)
