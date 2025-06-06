# Copyright 2019 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestStorageCategoryAllowNewProduct(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.areas.write({"pack_putaway_strategy": "ordered_locations"})
        cls.category = cls.pallets_location_storage_type.storage_category_id
        # Configure the rule matching Pallets to allow the same product on locations
        cls.category.allow_new_product_ids.allow_new_product = "same"

    def test_storage_category_allow_new_product(self):
        self.category.allow_new_product = "empty"
        self.assertEqual(self.category.get_allow_new_product(self.product), "empty")
        self.category.allow_new_product = "same_lot"
        self.assertEqual(self.category.get_allow_new_product(self.product), "same_lot")
        # Create a quant with a package of type Pallet to check the
        # allow_new_product rule result
        package_type_pallets = self.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )
        package = self.env["stock.quant.package"].create(
            {
                "name": "TEST PKG",
                "package_type_id": package_type_pallets.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.pallets_bin_2_location,
            1.0,
            package_id=package,
        )
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", self.pallets_bin_2_location.id),
                ("product_id", "=", self.product.id),
                ("package_id", "=", package.id),
            ]
        )
        self.assertEqual(
            self.category.get_allow_new_product(
                self.product,
                quants=quant,
                package_type=package_type_pallets,
                package=package,
            ),
            "same",
        )

    def test_storage_strategy_with_allow_new_product_rule(self):
        # Set pallets location type as only empty, while it also has a rule
        # that will force the 'allow_new_product' to 'same'
        self.pallets_location_storage_type.storage_category_id.write(
            {"allow_new_product": "empty"}
        )
        # Create picking
        in_picking = self.env["stock.picking"].create(
            {
                "picking_type_id": self.receipts_picking_type.id,
                "location_id": self.suppliers_location.id,
                "location_dest_id": self.input_location.id,
                "move_ids": [
                    (
                        0,
                        0,
                        {
                            "name": self.product.name,
                            "location_id": self.suppliers_location.id,
                            "location_dest_id": self.input_location.id,
                            "product_id": self.product.id,
                            "product_uom_qty": 96.0,
                            "product_uom": self.product.uom_id.id,
                        },
                    )
                ],
            }
        )
        # Mark as todo
        in_picking.action_confirm()
        # Put in pack
        in_picking.move_line_ids.qty_done = 48.0
        first_package = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        first_package.product_packaging_id = self.product_pallet_product_packaging
        # Put in pack again
        ml_without_package = in_picking.move_line_ids.filtered(
            lambda ml: not ml.result_package_id
        )
        ml_without_package.qty_done = 48.0
        second_pack = in_picking.action_put_in_pack()
        # Ensure packaging is set properly on pack
        second_pack.product_packaging_id = self.product_pallet_product_packaging

        # Validate picking
        in_picking.button_validate()
        # Assign internal picking
        int_picking = in_picking.move_ids.move_dest_ids.picking_id
        int_picking.action_assign()
        self.assertEqual(int_picking.location_dest_id, self.stock_location)
        self.assertEqual(
            int_picking.move_ids.mapped("location_dest_id"), self.stock_location
        )
        # First & second move lines goes into pallets bin 1, as forced by the rule
        self.assertEqual(
            int_picking.move_line_ids.mapped("location_dest_id"),
            self.pallets_bin_1_location,
        )

    def test_storage_category_mixed_allow_new_product(self):
        self.category.allow_new_product = "mixed"
        self.assertEqual(self.category.get_allow_new_product(self.product), "mixed")

        # Create a quant with a package of type Pallet to check the
        # allow_new_product rule result
        package_type_pallets = self.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )
        package_type_pallets_uk = self.env.ref(
            "stock_storage_type.package_storage_type_pallets_uk"
        )
        self.product2.package_type_id = package_type_pallets_uk
        package = self.env["stock.quant.package"].create(
            {
                "name": "TEST PKG",
                "package_type_id": package_type_pallets.id,
            }
        )
        package_uk = self.env["stock.quant.package"].create(
            {
                "name": "TEST PKG",
                "package_type_id": package_type_pallets_uk.id,
            }
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product,
            self.pallets_bin_2_location,
            1.0,
            package_id=package,
        )
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", self.pallets_bin_2_location.id),
                ("product_id", "=", self.product.id),
                ("package_id", "=", package.id),
            ]
        )
        self.assertEqual(
            self.category.get_allow_new_product(
                self.product2,
                quants=quant,
                package_type=package_type_pallets_uk,
                package=package_uk,
            ),
            "same",
        )
