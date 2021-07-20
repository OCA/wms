# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import fields

from odoo.addons.stock_reception_screen.tests.common import Common


class TestReceptionScreenMrpSubcontracting(Common):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._prepare_reception_screen()

    @classmethod
    def _prepare_reception_screen(cls):
        # product.product_delivery_02 has a subcontracted BoM defined with
        # 'mrp_subcontracting' installed
        cls.picking = cls._create_picking_in(partner=cls.env.ref("base.res_partner_12"))
        cls._create_picking_line(cls.picking, cls.product_2, 4)
        cls.picking.action_confirm()
        cls.picking.action_reception_screen_open()
        cls.screen = cls.picking.reception_screen_id

    def _record_components_for_picking(self, picking):
        for move in picking.move_lines:
            if not move.is_subcontract:
                continue
            context = dict(
                default_production_id=move.move_orig_ids.production_id.id,
                default_subcontract_move_id=move.id,
            )
            wiz_model = self.env["mrp.product.produce"].with_context(context)
            wiz = wiz_model.create({})
            for line in wiz.move_raw_ids.move_line_ids:
                line.qty_done = line.product_uom_qty
            wiz.do_produce()

    def test_reception_screen_with_subcontracted_products(self):
        """Receive subcontracted goods."""
        # Select the product to receive
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        # Receive 2/4 qties (corresponding to the product packaging qty)
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 2
        self.assertEqual(self.screen.current_move_line_qty_status, "lt")
        # Check package data (automatically filled normally)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_2_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_2_packaging.height)
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
        self.assertEqual(len(self.picking.move_lines), 1)
        self.screen.button_save_step()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-1")
        # The first 2 qties should be validated, creating a 2nd move to process
        self.assertEqual(len(self.picking.move_lines), 2)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 2
        self.assertEqual(self.screen.current_move_line_qty_status, "eq")
        self.screen.button_save_step()
        # Check package data (automatically filled as before)
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_2_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_2_packaging.height)
        self.screen.button_save_step()
        # Set location
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
        # Check that the manufacturing order is now done
        production = self.picking.move_lines.move_orig_ids.production_id
        self.assertEqual(production.state, "done")
        self.assertEqual(production.move_finished_ids.product_uom_qty, 4)
        self.assertEqual(production.move_finished_ids.quantity_done, 4)
        self.assertEqual(production.move_finished_ids.state, "done")
        for ml in production.finished_move_line_ids:
            self.assertEqual(ml.qty_done, 2)

    def test_reception_screen_with_subcontracted_products_with_tracked_components(self):
        """Receive subcontracted goods having components tracked by lots."""
        # Update the existing BoM to have a component tracked by lot
        bom_line = self.product_2.bom_ids.bom_line_ids
        component = bom_line.product_id.copy({"type": "product", "tracking": "lot"})
        bom_line.product_id = component
        component_lot = self.env["stock.production.lot"].create(
            {"product_id": component.id, "company_id": self.picking.company_id.id}
        )
        production = self.picking.move_lines.move_orig_ids.production_id
        self.env["stock.quant"]._update_available_quantity(
            component, production.move_raw_ids.location_id, 4, lot_id=component_lot
        )
        # Prepare a new reception
        self.picking.action_cancel()
        self._prepare_reception_screen()
        # Record components (mandatory)
        self._record_components_for_picking(self.picking)
        # Select the product to receive
        self.assertEqual(self.screen.current_step, "select_product")
        move = fields.first(self.screen.picking_filtered_move_lines)
        move.action_select_product()
        # Receive 2/4 qties (corresponding to the product packaging qty)
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 2
        self.assertEqual(self.screen.current_move_line_qty_status, "lt")
        # Check package data (automatically filled normally)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_2_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_2_packaging.height)
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
        self.assertEqual(len(self.picking.move_lines), 1)
        self.screen.button_save_step()
        self.assertEqual(move_line.result_package_id.name, "PID-TEST-1")
        # The first 2 qties should be validated, creating a 2nd move to process
        self.assertEqual(len(self.picking.move_lines), 2)
        self.screen.button_save_step()
        self.assertEqual(self.screen.current_step, "set_quantity")
        self.screen.current_move_line_qty_done = 2
        self.assertEqual(self.screen.current_move_line_qty_status, "eq")
        self.screen.button_save_step()
        # Check package data (automatically filled as before)
        self.assertEqual(self.screen.current_step, "select_packaging")
        self.assertEqual(self.screen.product_packaging_id, self.product_2_packaging)
        self.assertEqual(self.screen.package_storage_type_id, self.storage_type_pallet)
        self.assertEqual(self.screen.package_height, self.product_2_packaging.height)
        self.screen.button_save_step()
        # Set location
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
        # Check that the manufacturing order is now done
        production = self.picking.move_lines.move_orig_ids.production_id
        self.assertEqual(production.state, "done")
        self.assertEqual(production.move_finished_ids.product_uom_qty, 4)
        self.assertEqual(production.move_finished_ids.quantity_done, 4)
        self.assertEqual(production.move_finished_ids.state, "done")
        for ml in production.finished_move_line_ids:
            self.assertEqual(ml.qty_done, 2)
