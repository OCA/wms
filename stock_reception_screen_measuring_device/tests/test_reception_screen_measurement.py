# Copyright 2024 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo_test_helper import FakeModelLoader

from odoo.exceptions import UserError
from odoo.tests import tagged

from odoo.addons.component.tests.common import SavepointComponentRegistryCase

from .fake_components import FakeDevice


@tagged("-at_install", "post_install")
class TestReceptionScreenMeasurement(SavepointComponentRegistryCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.setUpModels()
        cls.setUpClassStorageType()
        cls.setUpClassProduct()
        cls.location_dest = cls.env.ref("stock.stock_location_stock")
        cls.location_src = cls.env.ref("stock.stock_location_suppliers")
        cls.warehouse = cls.env.ref("stock.warehouse0")
        cls.partner = cls.env.ref("base.res_partner_1")
        cls.setUpClassMeasuringDevice()
        cls.setUpClassComponents()

    @classmethod
    def setUpClassComponents(cls):
        cls._setup_registry(cls)
        cls._build_components(cls, FakeDevice)

    @classmethod
    def tearDownClass(cls):
        cls.loader.restore_registry()
        return super().tearDownClass()

    @classmethod
    def setUpModels(cls):
        cls.loader = FakeModelLoader(cls.env, cls.__module__)
        cls.loader.backup_registry()
        from .fake_models import FakeMeasuringDevice

        cls.loader.update_registry((FakeMeasuringDevice,))

    @classmethod
    def setUpClassMeasuringDevice(cls):
        cls.measuring_device = cls.env["measuring.device"].create(
            {
                "name": "TestDevice",
                "warehouse_id": cls.warehouse.id,
                "device_type": "fake",
                "is_default": True,
            }
        )

    @classmethod
    def setUpClassStorageType(cls):
        cls.location_storage_model = cls.env["stock.location.storage.type"]
        cls.location_boxes = cls.location_storage_model.create(
            {
                "name": "Boxes location",
            }
        )
        cls.location_pallets = cls.location_storage_model.create(
            {
                "name": "Pallets location",
            }
        )
        cls.storage_type_model = cls.env["stock.package.storage.type"]
        cls.storage_type_box = cls.storage_type_model.create(
            {
                "name": "BOX",
                "location_storage_type_ids": [(4, cls.location_boxes.id)],
            }
        )
        cls.storage_type_box_of_boxes = cls.storage_type_model.create(
            {
                "name": "BOX_OF_BOXES",
                "location_storage_type_ids": [(4, cls.location_boxes.id)],
            }
        )
        cls.storage_type_pallet = cls.storage_type_model.create(
            {
                "name": "PALLET",
                "location_storage_type_ids": [(4, cls.location_pallets.id)],
            }
        )

    @classmethod
    def setUpClassProduct(cls):
        cls.product_screw = cls.env["product.product"].create(
            {
                "name": "SCREWS",
                "type": "product",
            }
        )
        cls.packaging_model = cls.env["product.packaging"]
        cls.packaging_smaller_box = cls.packaging_model.create(
            {
                "name": "SMALLER BOX OF SCREWS",
                "product_id": cls.product_screw.id,
                "qty": 5,
                "package_storage_type_id": cls.storage_type_box.id,
            }
        )
        cls.packaging_regular_box = cls.packaging_model.create(
            {
                "name": "REGULAR BOX OF SCREWS",
                "product_id": cls.product_screw.id,
                "qty": 50,
                "package_storage_type_id": cls.storage_type_box.id,
            }
        )
        cls.packaging_huge_box = cls.packaging_model.create(
            {
                "name": "HUGE BOX OF SCREWS",
                "product_id": cls.product_screw.id,
                "qty": 500,
                "package_storage_type_id": cls.storage_type_box_of_boxes.id,
            }
        )
        cls.packaging_pallet = cls.packaging_model.create(
            {
                "name": "PALLET OF SCREWS",
                "product_id": cls.product_screw.id,
                "qty": 5000,
                "package_storage_type_id": cls.storage_type_pallet.id,
                "type_is_pallet": True,
            }
        )
        cls.all_packages_no_pallet = (
            cls.packaging_smaller_box
            | cls.packaging_regular_box
            | cls.packaging_huge_box
        )
        cls.all_packages = cls.all_packages_no_pallet | cls.packaging_pallet

    @classmethod
    def _create_picking_get_move_vals(cls, product_matrix):
        move_vals = []
        defaults = {
            "location_id": cls.location_src.id,
            "location_dest_id": cls.location_dest.id,
        }
        for product, qty in product_matrix:
            product_vals = {
                "product_id": product.id,
                "name": product.name,
                "product_uom_qty": qty,
                "product_uom": product.uom_id.id,
            }
            move_vals.append((0, 0, dict(defaults, **product_vals)))
        return move_vals

    @classmethod
    def _create_picking_get_values(cls, product_matrix):
        return {
            "partner_id": cls.partner.id,
            "location_id": cls.location_src.id,
            "location_dest_id": cls.location_dest.id,
            "picking_type_id": cls.env.ref("stock.picking_type_in").id,
            "move_lines": cls._create_picking_get_move_vals(product_matrix),
        }

    @classmethod
    def _create_picking_in(cls, product_matrix):
        picking_values = cls._create_picking_get_values(product_matrix)
        return cls.env["stock.picking"].create(picking_values)

    @classmethod
    def _picking_get_reception_screen(cls, picking):
        picking.action_confirm()
        picking.action_reception_screen_open()
        return picking.reception_screen_id

    @classmethod
    def _packaging_flush_dimensions(cls, packagings):
        field_names = ["max_weight", "packaging_length", "width", "height"]
        packagings.write({key: 0.0 for key in field_names})

    @classmethod
    def _packaging_get_default_dimensions(cls):
        field_names = ["max_weight", "packaging_length", "width", "height"]
        return {key: 42 for key in field_names}

    @classmethod
    def _packaging_set_dimensions(cls, packagings):
        packagings.write(cls._packaging_get_default_dimensions())

    def get_screen_at_packaging_selection(self, picking):
        move_screw = picking.move_lines[0]
        reception_screen = self._picking_get_reception_screen(picking)
        self.assertEqual(reception_screen.current_step, "select_product")
        move_screw.action_select_product()
        # Product isn't tracked by serial, next step is set_quantity
        self.assertEqual(reception_screen.current_step, "set_quantity")
        # receiving 800 out of 1000.0
        reception_screen.current_move_line_qty_done = 800
        self.assertEqual(reception_screen.current_move_line_qty_status, "lt")
        # Check package data (automatically filled normally)
        reception_screen.button_save_step()
        self.assertEqual(reception_screen.current_step, "select_packaging")
        return reception_screen

    def test_current_package_needs_measurement(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        # No dimension is set on the selected package
        reception_screen.product_packaging_id = self.packaging_huge_box
        self.assertTrue(reception_screen.package_has_missing_dimensions)
        # Setting dimensions sets the package_has_missing_dimensions to False
        self._packaging_set_dimensions(self.packaging_huge_box)
        reception_screen.invalidate_cache(["package_has_missing_dimensions"])
        self.assertFalse(reception_screen.package_has_missing_dimensions)

    def test_smaller_package_needs_measurement(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        # Select bigger package, set measurements, package_has_missing_dimensions
        # is set to False
        reception_screen.product_packaging_id = self.packaging_huge_box
        self._packaging_set_dimensions(self.packaging_huge_box)
        self.assertFalse(reception_screen.package_has_missing_dimensions)
        # However, regular and smaller boxes are missing measurements
        # smaller_package_has_missing_dimensions should be set to True
        self.assertTrue(reception_screen.smaller_package_has_missing_dimensions)
        # Set dimensions on regular box, smaller box is still missing dimensions
        self._packaging_set_dimensions(self.packaging_regular_box)
        reception_screen.invalidate_cache(["smaller_package_has_missing_dimensions"])
        self.assertTrue(reception_screen.smaller_package_has_missing_dimensions)
        # Set dimensions on smaller box, all dimensions are set on packages
        # smaller than the selected one
        self._packaging_set_dimensions(self.packaging_smaller_box)
        reception_screen.invalidate_cache(["smaller_package_has_missing_dimensions"])
        self.assertFalse(reception_screen.smaller_package_has_missing_dimensions)

    def test_measure_from_biggest_packaging_to_smallest(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        # select biggest package
        reception_screen.product_packaging_id = self.packaging_huge_box
        # Click the measure current package button
        reception_screen.measure_current_packaging()
        # Measuring device is assigned to the current package
        self.assertEqual(
            self.packaging_huge_box.measuring_device_id, self.measuring_device
        )
        # set dimensions on packaging using mocked measuring device
        measurement_values = {
            k: 42 for k in ("max_weight", "packaging_length", "width", "height")
        }
        self.measuring_device.mocked_measure(measurement_values)
        # Now measuring device is unassigned
        self.assertFalse(self.packaging_huge_box.measuring_device_id)
        # and all measurements are set on packaging
        for key, value in measurement_values.items():
            self.assertEqual(self.packaging_huge_box[key], value)
        # There's still smaller packages missing measurements
        self.assertTrue(reception_screen.smaller_package_has_missing_dimensions)
        # Click the measure smaller package button
        reception_screen.measure_smaller_packaging()
        # Among the 2 smaller packagings without dimension,
        # the biggest has the priority and should have been selected
        self.assertEqual(
            self.packaging_regular_box.measuring_device_id, self.measuring_device
        )
        # Set quantity, we still have a smaller packaging without measurement
        self.measuring_device.mocked_measure(measurement_values)
        for key, value in measurement_values.items():
            self.assertEqual(self.packaging_regular_box[key], value)
        reception_screen.invalidate_cache(["smaller_package_has_missing_dimensions"])
        self.assertTrue(reception_screen.smaller_package_has_missing_dimensions)
        # Select next smaller packaging for measurement, the smallest should be selected
        reception_screen.measure_smaller_packaging()
        self.assertEqual(
            self.packaging_smaller_box.measuring_device_id, self.measuring_device
        )
        # Set quantity, no more smaller packaging to measure,
        # smaller_package_has_missing_dimensions should be False
        self.measuring_device.mocked_measure(measurement_values)
        for key, value in measurement_values.items():
            self.assertEqual(self.packaging_smaller_box[key], value)
        reception_screen.invalidate_cache(["smaller_package_has_missing_dimensions"])
        self.assertFalse(reception_screen.smaller_package_has_missing_dimensions)

    def test_measuring_device_skips_measured_packagings(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        reception_screen.product_packaging_id = self.packaging_huge_box
        # Set dimensions on bigger and regular box
        self._packaging_set_dimensions(
            self.packaging_huge_box | self.packaging_regular_box
        )
        self.assertFalse(reception_screen.package_has_missing_dimensions)
        self.assertTrue(reception_screen.smaller_package_has_missing_dimensions)
        # Selected packaging for measurement should be packaging_smaller_box
        reception_screen.measure_smaller_packaging()
        self.assertEqual(
            self.packaging_smaller_box.measuring_device_id, self.measuring_device
        )

    def test_measurement_device_cancel_package_measurement(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        reception_screen.product_packaging_id = self.packaging_huge_box
        # Select huge packaging
        reception_screen.measure_current_packaging()
        self.assertTrue(self.packaging_huge_box.measuring_device_id)
        reception_screen.cancel_measure_current_packaging()
        self.assertFalse(self.packaging_huge_box.measuring_device_id)
        # Assigning measuring device to regular packaging then pressing the cancel
        # should unassign the measuring device
        reception_screen.measure_smaller_packaging()
        self.assertTrue(self.packaging_regular_box.measuring_device_id)
        reception_screen.cancel_measure_current_packaging()
        self.assertFalse(self.packaging_regular_box.measuring_device_id)

    def test_measuring_device_cannot_be_assigned_twice(self):
        picking = self._create_picking_in([(self.product_screw, 1000.0)])
        picking.action_confirm()
        reception_screen = self.get_screen_at_packaging_selection(picking)
        # Select huge box as packaging
        reception_screen.product_packaging_id = self.packaging_huge_box
        # Assign device to huge box packaging
        reception_screen.measure_current_packaging()
        self.assertTrue(self.packaging_huge_box.measuring_device_id)
        # Then try to assign device to regular box packaging, and check
        # that it had no effect
        message = r"Measurement machine already in use."
        with self.assertRaisesRegex(UserError, message):
            reception_screen.measure_smaller_packaging()
        self.assertFalse(self.packaging_regular_box.measuring_device_id)
