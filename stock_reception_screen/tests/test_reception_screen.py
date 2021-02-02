# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import exceptions, fields
from odoo.tests.common import SavepointCase


class TestReceptionScreen(SavepointCase):
    at_install = False
    post_install = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )
        cls.storage_type_pallet.barcode = "123"
        cls.product = cls.env.ref("product.product_delivery_01")
        cls.product.tracking = "lot"
        cls.product_packaging = cls.env["product.packaging"].create(
            {
                "name": "PKG TEST",
                "product_id": cls.product.id,
                "qty": 4,
                "package_storage_type_id": cls.storage_type_pallet.id,
                "height": 200,
                "width": 500,
                "lngth": 500,
                "max_weight": 10,
            }
        )
        cls.product_2 = cls.env.ref("product.product_delivery_02")
        cls.product_2.tracking = "none"
        cls.product_2_packaging = cls.env["product.packaging"].create(
            {
                "name": "PKG TEST 2",
                "product_id": cls.product_2.id,
                "qty": 2,
                "package_storage_type_id": cls.storage_type_pallet.id,
                "height": 200,
                "width": 500,
                "lngth": 500,
                "max_weight": 10,
            }
        )
        cls.location_dest = cls.env.ref("stock.stock_location_stock")
        cls.location_src = cls.env.ref("stock.stock_location_suppliers")
        cls.picking = cls.env["stock.picking"].create(
            {
                "partner_id": cls.env.ref("base.res_partner_1").id,
                "location_id": cls.location_src.id,
                "location_dest_id": cls.location_dest.id,
                "picking_type_id": cls.env.ref("stock.picking_type_in").id,
                "move_lines": [
                    (
                        0,
                        False,
                        {
                            "name": cls.product.display_name,
                            "product_id": cls.product.id,
                            "product_uom": cls.product.uom_id.id,
                            "product_uom_qty": 10,
                            "location_id": cls.location_src.id,
                            "location_dest_id": cls.location_dest.id,
                        },
                    ),
                    (
                        0,
                        False,
                        {
                            "name": cls.product_2.display_name,
                            "product_id": cls.product_2.id,
                            "product_uom": cls.product_2.uom_id.id,
                            "product_uom_qty": 10,
                            "location_id": cls.location_src.id,
                            "location_dest_id": cls.location_dest.id,
                        },
                    ),
                ],
            }
        )
        cls.picking.action_confirm()
        cls.picking.action_reception_screen_open()
        cls.screen = cls.picking.reception_screen_id

    def test_reception_screen(self):
        # Select the product to receive
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        # Create the lot
        self.assertEqual(self.screen.current_step, "set_lot_number")
        self.screen.on_barcode_scanned_set_lot_number("LOT-TEST-1")
        # Set the expiry date on the lot
        self.assertEqual(self.screen.current_step, "set_expiry_date")
        self.screen.current_move_line_lot_life_date = fields.Datetime.today()
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_quantity")
        # Receive 4/10 qties (corresponding to the product packaging qty)
        self.screen.current_move_line_qty_done = 4
        self.assertEqual(self.screen.current_move_line_qty_status, "lt")
        # Check package data (automatically filled normally)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_packaging.height)
        # Check that a destination location is defined by default
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        self.screen.current_move_line_location_dest_stored_id = self.location_dest
        self.screen.button_save_step()
        self.assertEqual(
            self.screen.current_move_line_location_dest_id,
            self.screen.current_move_line_location_dest_stored_id,
        )
        # Set a package
        self.assertEqual(self.screen.current_step, "set_package")
        self.screen.current_move_line_package = "PID-TEST-1"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-1")
        move_line = self.screen.current_move_line_id
        self.assertFalse(move_line.result_package_id)
        self.assertEqual(len(self.picking.move_lines), 2)
        self.screen.button_save_step()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-1")
        # The first 4 qties should be validated, creating a 2nd move to process
        self.assertEqual(len(self.picking.move_lines), 3)
        self.assertEqual(self.screen.current_step, "set_lot_number")

        self.assertEqual(self.screen.current_step, "set_lot_number")
        self.assertEqual(self.screen.current_move_line_lot_id.name, "LOT-TEST-1")
        self.screen.on_barcode_scanned_set_lot_number("LOT-TEST-2")
        self.assertEqual(self.screen.current_step, "set_expiry_date")
        self.screen.current_move_line_lot_life_date = fields.Datetime.today()
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 6
        self.assertEqual(self.screen.current_move_line_qty_status, "eq")
        # Check package data (not automatically filled as no packaging match)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertFalse(self.screen.product_packaging_id)
        self.assertFalse(self.screen.package_storage_type_id)
        self.assertFalse(self.screen.package_height)
        # Set mandatory package data
        self.screen.package_storage_type_id = self.storage_type_pallet
        self.screen.package_height = 20
        # Set location
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        self.screen.current_move_line_location_dest_stored_id = self.location_dest
        # Set a package
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_package")
        self.screen.current_move_line_package = "PID-TEST-2"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-2")
        move_line = self.screen.current_move_line_id
        self.assertFalse(move_line.result_package_id)
        self.screen.button_save_step()  # Reception done
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-2")

        # Receive 2nd product
        self.assertEqual(self.screen.current_step, "select_product")
        self.assertEqual(len(self.picking.move_lines), 3)
        # Check the one move left to do
        move_left = self.picking.move_lines.filtered(lambda m: m.state != "done")
        self.assertEqual(len(move_left), 1)
        move_left.action_select_product()
        self.assertEqual(len(self.screen.current_move_line_lot_id), 0)
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 20
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.screen.package_storage_type_id = self.storage_type_pallet
        self.screen.package_height = 20
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        self.screen.current_move_line_location_dest_stored_id = self.location_dest
        self.screen.button_save_step()
        self.assertEqual(
            self.screen.current_move_line_location_dest_id,
            self.screen.current_move_line_location_dest_stored_id,
        )
        self.assertEqual(self.screen.current_step, "set_package")
        self.screen.current_move_line_package = "PID-TEST-2.1"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-2.1")
        move_line = self.screen.current_move_line_id
        self.assertFalse(move_line.result_package_id)
        self.screen.button_save_step()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-2.1")
        self.assertEqual(self.screen.current_step, "done")
        move_states = self.picking.move_lines.mapped("state")
        self.assertTrue(all([state == "done" for state in move_states]))

    def test_reception_screen_next_pack(self):
        # Select the product to receive
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        # Create the lot
        self.assertEqual(self.screen.current_step, "set_lot_number")
        self.screen.on_barcode_scanned_set_lot_number("LOT-TEST-1")
        # Set the expiry date on the lot
        self.assertEqual(self.screen.current_step, "set_expiry_date")
        self.screen.current_move_line_lot_life_date = fields.Datetime.today()
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_quantity")
        # Receive 4/10 qties (corresponding to the product packaging qty)
        self.screen.current_move_line_qty_done = 4
        self.assertEqual(self.screen.current_move_line_qty_status, "lt")
        # Check package data (automatically filled normally)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_packaging.height)
        # Check that a destination location is defined by default
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_location")
        self.screen.current_move_line_location_dest_stored_id = self.location_dest
        self.screen.button_save_step()
        self.assertEqual(
            self.screen.current_move_line_location_dest_id,
            self.screen.current_move_line_location_dest_stored_id,
        )
        # Set a package
        self.assertEqual(self.screen.current_step, "set_package")
        self.screen.current_move_line_package = "PID-TEST-1"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-1")
        move_line = self.screen.current_move_line_id
        self.assertFalse(move_line.result_package_id)
        self.screen.button_next_pack()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-1")
        # Iterate on the same product/lot to scan the second package
        self.assertEqual(self.screen.current_move_line_qty_done, 4)
        self.assertTrue(self.screen.current_move_line_location_dest_stored_id)
        self.assertEqual(self.screen.product_packaging_id, self.product_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_packaging.height)
        self.assertEqual(self.screen.current_step, "set_package")
        self.screen.current_move_line_package = "PID-TEST-2"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-2")
        move_line = self.screen.current_move_line_id
        self.screen.button_next_pack()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-2")
        # Third package
        self.screen.current_move_line_package = "PID-TEST-3"
        self.assertEqual(self.screen.current_move_line_package_stored, "PID-TEST-3")
        move_line = self.screen.current_move_line_id
        self.assertFalse(move_line.result_package_id)
        self.screen.button_next_pack()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-3")
        # At this stage we receive 4*3 = 12 quantities while we were waiting for 10,
        # it's not an issue.
        move_lines = self.picking.move_line_ids.filtered(
            lambda l: "PID-TEST-" in (l.result_package_id.name or "")
        )
        qty_received = sum(move_lines.mapped("qty_done"))
        self.assertEqual(qty_received, 12)
        # All the product/lot has been processed, the operator can now select
        # another product
        self.assertEqual(self.screen.current_step, "select_product")

    def test_reception_screen_check_state(self):
        self.product.tracking = "none"
        # Select the product to receive
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        self.assertEqual(self.screen.current_step, "set_quantity")
        # And validate the picking behind the scene while we are processing it
        # with the reception screen
        for move in self.picking.move_lines:
            move.quantity_done = move.product_uom_qty
        self.picking.action_done()
        self.assertEqual(self.picking.state, "done")
        # Continue the work on the reception screen by receiving some qty:
        # an error should be raised
        self.screen.current_move_line_qty_done = 4
        with self.assertRaises(exceptions.UserError):
            self.screen.button_save_step()

    def test_reception_screen_scan_storage_type(self):
        """ Tests the scanning of a storage type.
        """
        # Moves until the screen in which we select a packaging.
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        self.screen.on_barcode_scanned_set_lot_number("LOT-TEST-1")
        self.screen.current_move_line_lot_life_date = fields.Datetime.today()
        self.screen.button_save_step()
        self.screen.current_move_line_qty_done = 1
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertFalse(self.screen.product_packaging_id)
        self.assertFalse(self.screen.package_storage_type_id)
        self.assertFalse(self.screen.package_height)

        # Scans the barcode of the storage type, this will select automatically
        # the storage type and the packaging.
        self.screen.on_barcode_scanned_select_packaging(
            self.storage_type_pallet.barcode
        )
        self.assertEqual(self.screen.product_packaging_id, self.product_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_packaging.height)
