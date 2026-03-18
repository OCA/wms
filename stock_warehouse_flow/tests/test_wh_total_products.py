# © 2026 FactorLibre - Adriana Saiz <adriana.saiz@factorlibre.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.tests.common import TransactionCase


class TestWhTotalProducts(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.wh1 = cls.env.ref("stock.warehouse0")
        cls.wh2 = cls.env["stock.warehouse"].create(
            {
                "name": "Warehouse 2",
                "code": "WH2",
                "company_id": cls.wh1.company_id.id,
            }
        )
        cls.partner = cls.env["res.partner"].create({"name": "Test Partner"})
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
                "list_price": 10.0,
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
                "list_price": 20.0,
            }
        )
        cls.product_c = cls.env["product.product"].create(
            {
                "name": "Product C",
                "type": "product",
                "list_price": 30.0,
            }
        )
        cls.loc_customer = cls.env.ref("stock.stock_location_customers")
        # Disable flow application on delivery routes to avoid interference
        # with flow demo data — we only test the compute field here
        cls.wh1.delivery_route_id.apply_flow_on = False
        cls.wh2.delivery_route_id.apply_flow_on = False

    def _create_sale_order(self, lines):
        return self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "warehouse_id": self.wh1.id,
                "order_line": [
                    (
                        0,
                        0,
                        {
                            "product_id": product.id,
                            "product_uom_qty": qty,
                        },
                    )
                    for product, qty in lines
                ],
            }
        )

    def _create_move(self, order_line, warehouse, qty=None):
        """Create a stock move linked to a sale order line.

        Simulates the result of procurement with different warehouses,
        which in production is done by sale_warehouse_allocation
        (omnichannel module) that assigns different routes per line.
        """
        return self.env["stock.move"].create(
            {
                "name": order_line.product_id.name,
                "product_id": order_line.product_id.id,
                "product_uom_qty": qty or order_line.product_uom_qty,
                "product_uom": order_line.product_uom.id,
                "sale_line_id": order_line.id,
                "location_id": warehouse.lot_stock_id.id,
                "location_dest_id": self.loc_customer.id,
                "warehouse_id": warehouse.id,
                "picking_type_id": warehouse.out_type_id.id,
            }
        )

    def test_single_warehouse_all_moves(self):
        """All moves in one warehouse: wh_total_products = SO total."""
        order = self._create_sale_order(
            [
                (self.product_a, 5),
                (self.product_b, 10),
                (self.product_c, 3),
            ]
        )
        moves = self.env["stock.move"]
        for line in order.order_line:
            moves |= self._create_move(line, self.wh1)

        self.assertEqual(len(moves), 3)
        self.assertEqual(set(moves.mapped("wh_total_products")), {18.0})

    def test_multi_warehouse_split(self):
        """Moves split across 2 warehouses: each sees only its share.

        Simulates omnichannel scenario where sale_warehouse_allocation
        routes SO lines to different warehouses based on stock.
        """
        order = self._create_sale_order(
            [
                (self.product_a, 5),
                (self.product_b, 10),
                (self.product_c, 3),
            ]
        )
        lines = order.order_line.sorted("id")
        # WH1 gets product_a (5) + product_b (10) = 15
        move_a = self._create_move(lines[0], self.wh1)
        move_b = self._create_move(lines[1], self.wh1)
        # WH2 gets product_c (3)
        move_c = self._create_move(lines[2], self.wh2)

        self.assertEqual(move_a.wh_total_products, 15.0)
        self.assertEqual(move_b.wh_total_products, 15.0)
        self.assertEqual(move_c.wh_total_products, 3.0)

    def test_no_sale_line_fallback(self):
        """Move without sale_line_id returns its own qty."""
        move = self.env["stock.move"].create(
            {
                "name": "Manual move",
                "product_id": self.product_a.id,
                "product_uom_qty": 7,
                "product_uom": self.product_a.uom_id.id,
                "location_id": self.wh1.lot_stock_id.id,
                "location_dest_id": self.loc_customer.id,
                "warehouse_id": self.wh1.id,
                "picking_type_id": self.wh1.out_type_id.id,
            }
        )
        self.assertEqual(move.wh_total_products, 7.0)

    def test_cancelled_moves_excluded(self):
        """Cancelled moves are not counted in wh_total_products."""
        order = self._create_sale_order(
            [
                (self.product_a, 5),
                (self.product_b, 10),
            ]
        )
        lines = order.order_line.sorted("id")
        move_a = self._create_move(lines[0], self.wh1)
        move_b = self._create_move(lines[1], self.wh1)

        self.assertEqual(move_a.wh_total_products, 15.0)

        # Cancel move_b
        move_b._action_cancel()
        # Invalidate ORM cache: non-stored compute won't auto-refresh
        # when a sibling move changes state
        self.env.invalidate_all()

        self.assertEqual(move_a.wh_total_products, 5.0)

    def test_flow_domain_filters_by_wh_total(self):
        """Flow domain using wh_total_products filters moves correctly.

        Creates two moves from the same SO in different warehouses,
        then verifies that a flow domain [('wh_total_products', '>', 1)]
        matches only the move whose warehouse total exceeds 1.
        This is the core use case: mono-line vs multi-line routing.
        """
        order = self._create_sale_order(
            [
                (self.product_a, 1),
                (self.product_b, 3),
            ]
        )
        lines = order.order_line.sorted("id")
        move_wh1 = self._create_move(lines[0], self.wh1)  # 1 unit
        move_wh2 = self._create_move(lines[1], self.wh2)  # 3 units

        # Create a flow with move_domain filtering by wh_total_products
        flow = self.env["stock.warehouse.flow"].create(
            {
                "name": "Multi-line flow",
                "warehouse_id": self.wh1.id,
                "from_picking_type_id": self.wh1.out_type_id.id,
                "to_picking_type_id": self.wh1.out_type_id.id,
                "move_domain": "[('wh_total_products', '>', 1)]",
            }
        )

        # Domain should NOT match move_wh1 (wh_total=1, not > 1)
        self.assertFalse(flow._is_domain_valid_for_move(move_wh1))
        # Domain SHOULD match move_wh2 (wh_total=3, > 1)
        self.assertTrue(flow._is_domain_valid_for_move(move_wh2))

    def test_single_line_per_warehouse(self):
        """Each warehouse has one line: wh_total_products = line qty.

        Simulates: SO with Shirt(1) → Warehouse, Pants(3) → Store.
        Global total_products would be 4, but each warehouse should
        only see its own qty (1 and 3 respectively), so flow domains
        like [('wh_total_products', '>', 1)] route correctly
        (mono-line vs multi-line).
        """
        order = self._create_sale_order(
            [
                (self.product_a, 1),
                (self.product_b, 3),
            ]
        )
        lines = order.order_line.sorted("id")
        # Warehouse gets product_a (1 unit)
        move_shirt = self._create_move(lines[0], self.wh1)
        # Store gets product_b (3 units)
        move_pants = self._create_move(lines[1], self.wh2)

        # Each warehouse sees only its own qty, not the global 4
        self.assertEqual(move_shirt.wh_total_products, 1.0)
        self.assertEqual(move_pants.wh_total_products, 3.0)

    def test_incoming_moves_excluded(self):
        """Incoming (return) moves are excluded from wh_total_products.

        Exchange claims generate both incoming (return) and outgoing (new
        shipment) moves under the same sale.order. Only outgoing moves
        should count to avoid inflating the total.
        """
        order = self._create_sale_order(
            [
                (self.product_a, 1),
                (self.product_b, 1),
            ]
        )
        lines = order.order_line.sorted("id")
        # Outgoing moves (new shipment)
        move_out_a = self._create_move(lines[0], self.wh1)
        move_out_b = self._create_move(lines[1], self.wh1)
        # Incoming move (return) — same SO, same warehouse
        move_in = self.env["stock.move"].create(
            {
                "name": "Return %s" % self.product_a.name,
                "product_id": self.product_a.id,
                "product_uom_qty": 1,
                "product_uom": self.product_a.uom_id.id,
                "sale_line_id": lines[0].id,
                "location_id": self.loc_customer.id,
                "location_dest_id": self.wh1.lot_stock_id.id,
                "warehouse_id": self.wh1.id,
                "picking_type_id": self.wh1.in_type_id.id,
            }
        )
        # Incoming move should NOT inflate the outgoing total
        self.assertEqual(move_out_a.wh_total_products, 2.0)
        self.assertEqual(move_out_b.wh_total_products, 2.0)
        # Incoming move with sale_line_id sees outgoing siblings total
        # (irrelevant in practice: flows only evaluate outgoing moves)
        self.assertEqual(move_in.wh_total_products, 2.0)

    def test_single_warehouse_via_so_confirm(self):
        """Integration: SO confirm generates moves with correct field."""
        order = self._create_sale_order(
            [
                (self.product_a, 5),
                (self.product_b, 10),
            ]
        )
        order.action_confirm()
        moves = self.env["stock.move"].search(
            [("sale_line_id.order_id", "=", order.id)]
        )
        self.assertEqual(len(moves), 2)
        for move in moves:
            self.assertEqual(move.wh_total_products, 15.0)
