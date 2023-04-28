# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestAutoAssignStorageType(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_packaging = cls.product_lot_pallets_product_packaging
        cls.package_storage_type = cls.product_packaging.package_type_id

        # Create a new package type for auto assignation
        vals = {
            "name": "Auto Assigned Package Type",
        }
        cls.auto_assigned_package_type = cls.env["stock.package.type"].create(vals)

    def test_auto_assign_package_storage_type_without_packaging_id(self):
        """Packages without `packaging_id` are internal packages and they
        are intended to be stored in the warehouse.
        On such packages storage type is automatically defined.
        """
        package = self.env["stock.quant.package"].create(
            {"name": "TEST", "product_packaging_id": self.product_packaging.id}
        )
        self.assertEqual(package.package_type_id, self.package_storage_type)

    def test_auto_assign_packaging(self):
        """
        Test the auto assignation for package type from
        the default package type on the product

        - Set the default package type on the product
        - Create a move and validate it
        - The package type should be set on package
        """

        # Set a default package on the product
        self.product.package_type_id = self.auto_assigned_package_type

        confirmed_move = self._create_single_move(self.product)
        confirmed_move.location_dest_id = self.pallets_bin_1_location
        confirmed_move._assign_picking()
        self._update_qty_in_location(
            confirmed_move.location_id,
            confirmed_move.product_id,
            confirmed_move.product_qty,
        )
        confirmed_move._action_assign()
        picking = confirmed_move.picking_id
        picking.action_confirm()
        picking.move_line_ids.qty_done = 10.0
        first_package = picking.action_put_in_pack()

        picking.button_validate()

        self.assertEqual(self.auto_assigned_package_type, first_package.package_type_id)

    def test_auto_assign_no_packaging(self):
        """
        Test the non auto assignation for package type from
        the default package type on the product

        - Unset the default package type on the product
        - Create a move and validate it
        - The package type should not be set on package
        """

        # Set a default package on the product
        self.product.package_type_id = False

        confirmed_move = self._create_single_move(self.product)
        confirmed_move.location_dest_id = self.pallets_bin_1_location
        confirmed_move._assign_picking()
        self._update_qty_in_location(
            confirmed_move.location_id,
            confirmed_move.product_id,
            confirmed_move.product_qty,
        )
        confirmed_move._action_assign()
        picking = confirmed_move.picking_id
        picking.action_confirm()
        picking.move_line_ids.qty_done = 10.0
        first_package = picking.action_put_in_pack()

        picking.button_validate()

        self.assertFalse(first_package.package_type_id)
