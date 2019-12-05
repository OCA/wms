# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields
from odoo.tests.common import SavepointCase


class TestReceptionScreen(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets")
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product_packaging = cls.env["product.packaging"].create(
            {
                "name": "PKG TEST",
                "product_id": cls.product.id,
                "qty": 4,
                "stock_package_storage_type_id": cls.storage_type_pallet.id,
                "height": 10,
            }
        )
        cls.location_dest = cls.env.ref("stock.stock_location_stock")
        cls.location_src = cls.env.ref("stock.stock_location_suppliers")
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "picking_type_id": cls.env.ref("stock.chi_picking_type_in").id,
                "move_lines": [
                    (0, False, {
                        "name": cls.product.display_name,
                        "product_id": cls.product.id,
                        "product_uom": cls.product.uom_id.id,
                        "product_uom_qty": 10,
                        "location_id": cls.location_src.id,
                        "location_dest_id": cls.location_dest.id,
                    })
                ]
            }
        )
        cls.picking.action_confirm()
        cls.picking.action_reception_screen_open()
        cls.screen = cls.picking.reception_screen_id

    def test_reception_screen(self):
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        self.assertEqual(self.screen.current_step, "set_quantity")
        # Receive 4/10 qties (corresponding to the product packaging qty)
        self.screen.current_move_line_qty_done = 4
        self.assertEqual(self.screen.current_move_line_qty_status, "lt")
        # Check that a destination location is defined by default
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        self.assertTrue(self.screen.current_move_location_dest_id)
        # Set a package (PID)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_pid")
        self.screen.current_move_line_pid = "PID-TEST-1"
        self.assertEqual(
            self.screen.current_move_line_id.result_package_id.name,
            "PID-TEST-1"
        )
        # Check package data (automatically filled normally)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(
            self.screen.current_move_line_product_packaging_id,
            self.product_packaging
        )
        self.assertEqual(
            self.screen.current_move_line_storage_type,
            self.storage_type_pallet
        )
        self.assertEqual(
            self.screen.current_move_line_height,
            self.product_packaging.height
        )
        # The first 4 qties should be validated, creating a 2nd move to process
        self.assertEqual(len(self.picking.move_lines), 1)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_product")
        self.assertEqual(len(self.picking.move_lines), 2)
        # Check the validated move
        move_done = self.picking.move_lines.filtered(
            lambda m: m.state == "done")
        self.assertEqual(len(move_done.move_line_ids), 1)
        self.assertEqual(
            move_done.move_line_ids.result_package_id.name, "PID-TEST-1")
        # Receive the remaining 6 qties
        move = fields.first(
            self.screen.picking_filtered_move_lines.filtered(
                lambda m: not m.quantity_done))
        move.action_select_product()
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 6
        self.assertEqual(self.screen.current_move_line_qty_status, "eq")
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        # Set a package (PID)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_pid")
        self.screen.current_move_line_pid = "PID-TEST-2"
        self.assertEqual(
            self.screen.current_move_line_id.result_package_id.name,
            "PID-TEST-2"
        )
        # Check package data (not automatically filled as no packaging match)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertFalse(
            self.screen.current_move_line_product_packaging_id,
        )
        self.assertFalse(
            self.screen.current_move_line_storage_type,
        )
        self.assertFalse(self.screen.current_move_line_height)
        # Set mandatory package data
        self.screen.current_move_line_storage_type = self.storage_type_pallet
        self.screen.current_move_line_height = 20
        # Reception done
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "done")
        self.assertEqual(len(self.picking.move_lines), 2)
        move_states = self.picking.move_lines.mapped("state")
        self.assertTrue(all([state == "done" for state in move_states]))
