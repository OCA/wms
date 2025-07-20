# Copyright 2023 Michael Tietz (MT Software) <mtietz@mt-software.de>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.addons.stock.tests.common import TestStockCommon


class TestStockFullLocationReservationCommon(TestStockCommon):
    @classmethod
    def setUpClass(cls):
        super(TestStockFullLocationReservationCommon, cls).setUpClass()
        cls.picking_type = cls.env.ref("stock.picking_type_out")
        cls.picking_type.is_full_location_reservation_visible = True
        cls.location = cls.env.ref("stock.stock_location_stock")
        cls.location_rack = cls.location.create(
            {"name": "Rack", "location_id": cls.location.id}
        )
        cls.location_rack_child = cls.location.create(
            {"name": "Rack child", "location_id": cls.location_rack.id}
        )
        cls.customer_location = cls.env.ref("stock.stock_location_customers")

    def _create_quant(self, product, location, qty, package=None):
        package_id = package and package.id
        return self.env["stock.quant"].create(
            {
                "product_id": product.id,
                "location_id": location.id,
                "quantity": qty,
                "package_id": package_id,
            }
        )

    def _create_quants(self, vals):
        for val in vals:
            self._create_quant(*val)

    def _create_move(self, picking, product, qty, package=None):
        package_level_id = False
        if package:
            package_level_id = (
                self.env["stock.package_level"]
                .create({"package_id": package.id, "company_id": picking.company_id.id})
                .id
            )
        return self.MoveObj.create(
            {
                "name": product.name,
                "product_id": product.id,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
                "picking_id": picking.id,
                "location_id": picking.location_id.id,
                "location_dest_id": picking.location_dest_id.id,
                "package_level_id": package_level_id,
            }
        )

    def _create_picking(self, location, location_dest, picking_type, moves):
        picking = self.PickingObj.create(
            {
                "picking_type_id": picking_type.id,
                "location_id": location.id,
                "location_dest_id": location_dest.id,
            }
        )
        for move in moves:
            vals = [picking] + move
            self._create_move(*vals)
        return picking

    def _check_move_line_len(self, pick, length, filter_func=None):
        moves = pick.move_lines
        if filter_func:
            moves = moves.filtered(filter_func)

        self.assertEqual(
            len(moves),
            length,
        )

    def _filter_func(self, m):
        return m.is_full_location_reservation
