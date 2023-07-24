# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.exceptions import UserError
from odoo.tests import SavepointCase
from odoo.tests.common import Form


class TestStockUniqueOrderPerLocation(SavepointCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))

        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.warehouse.delivery_steps = "pick_pack_ship"
        cls.pick_type = cls.warehouse.pick_type_id
        cls.location = cls.pick_type.default_location_dest_id
        cls.dispatch_location = cls.env.ref("stock.location_dispatch_zone")
        cls.customer_location = cls.env.ref("stock.stock_location_customers")
        cls.packing_location = cls.env.ref("stock.location_pack_zone")
        cls.customer = cls.env["res.partner"].sudo().create({"name": "Customer"})
        cls.product_a = cls.env["product.product"].create(
            {
                "name": "Product A",
                "type": "product",
            }
        )
        cls.product_b = cls.env["product.product"].create(
            {
                "name": "Product B",
                "type": "product",
            }
        )
        # # Create a picking to do
        cls.pick = cls._create_picking(cls.pick_type, lines=[(cls.product_a, 10)])
        cls._update_qty_in_location(cls.location, cls.product_a, 10)
        cls.pick.action_assign()
        # Create another picking that will be used as next picking in the chain
        cls.pick_type_out = cls.env.ref("stock.picking_type_out")
        cls.pick_next = cls._create_picking(
            cls.pick_type_out, lines=[(cls.product_b, 10)]
        )
        cls._update_qty_in_location(cls.pick_next.location_dest_id, cls.product_b, 10)
        cls.pick_next.action_assign()
        # # Create a reserved move at destination
        cls.reserving_move = cls.env["stock.move"].create(
            {
                "name": "Assigned move",
                "product_id": cls.product_a.id,
                "product_uom_qty": 3,
                "product_uom": cls.product_a.uom_id.id,
                "location_id": cls.packing_location.id,
                "location_dest_id": cls.customer_location.id,
                "picking_id": cls.pick_next.id,
            }
        )
        cls._update_qty_in_location(cls.packing_location, cls.product_a, 3)
        cls.reserving_move._action_confirm()
        cls.reserving_move._action_assign()
        assert cls.reserving_move.state == "assigned"

    @classmethod
    def _create_picking(cls, picking_type, lines):
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = picking_type
        picking_form.partner_id = cls.customer
        for product, qty in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = product
                move.product_uom_qty = qty
        picking = picking_form.save()
        picking.action_confirm()
        return picking

    @classmethod
    def _update_qty_in_location(cls, location, product, quantity):
        quants = cls.env["stock.quant"]._gather(product, location, strict=True)
        # this method adds the quantity to the current quantity, so remove it
        quantity -= sum(quants.mapped("quantity"))
        cls.env["stock.quant"]._update_available_quantity(product, location, quantity)

    def test_set_quantity_location_empty(self):
        """Check transfer to an empty location.

        Transfer succesful.

        """
        self.pick_type.same_next_picking = True
        self.reserving_move._action_cancel()
        self._update_qty_in_location(self.packing_location, self.product_a, 0)
        # Check destination location is empty
        self.assertFalse(self.packing_location.quant_ids.quantity)
        self.assertFalse(self.packing_location.quant_ids.reserved_quantity)
        for move in self.pick.move_lines:
            move.quantity_done = move.product_uom_qty
        self.pick._action_done()
        self.assertEqual(self.pick.state, "done")

    def test_set_quantity_move_at_location_same_next_picking(self):
        """Check transfer to a location with a move with same new picking.

        Transfer successful.

        """
        self.pick_type.same_next_picking = True
        # Set destination move to be from the next picking
        self.pick.move_lines.move_dest_ids = [(4, self.pick_next.move_lines[0].id, 0)]
        for move in self.pick.move_lines:
            move.quantity_done = move.product_uom_qty
        self.pick._action_done()
        self.assertEqual(self.pick.state, "done")

    def test_set_quantity_move_at_location_not_same_next_picking(self):
        """Check transfer to location with move different next picking.

        Transfer no accepted.

        """
        self.pick_type.same_next_picking = True
        for move in self.pick.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(UserError):
            self.pick._action_done()
        # Check allowed when disabling the option
        self.pick_type.same_next_picking = False
        self.pick._action_done()
        self.assertEqual(self.pick.state, "done")

    def test_set_quantity_move_at_location_with_unassign_quantity(self):
        """Check transfer to location with some product not assigned

        Transfer no accepted.

        """
        self.pick_type.same_next_picking = True
        self.reserving_move._action_cancel()
        self._update_qty_in_location(self.packing_location, self.product_a, 4)
        for move in self.pick.move_lines:
            move.quantity_done = move.product_uom_qty
        with self.assertRaises(UserError):
            self.pick._action_done()
