# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from .common import TestStorageTypeCommon


class TestAutoAssignStorageType(TestStorageTypeCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_packaging = cls.product_lot_pallets_product_packaging
        cls.package_storage_type = cls.product_packaging.package_storage_type_id

    def test_auto_assign_package_storage_type_without_packaging_id(self):
        """Packages without `packaging_id` are internal packages and they
        are intended to be stored in the warehouse.
        On such packages storage type is automatically defined.
        """
        package = self.env["stock.quant.package"].create(
            {"name": "TEST", "product_packaging_id": self.product_packaging.id}
        )
        self.assertEqual(package.package_storage_type_id, self.package_storage_type)

    def test_auto_assign_package_storage_type_with_packaging_id(self):
        """Packages with `packaging_id` are delivery packages and they are not
        intended to be stored in the warehouse.
        On such packages storage type is not set.
        """
        # Set a delivery packaging (which is a product.packaging without product_id set)
        packaging = self.env["product.packaging"].create({"name": "TEST"})
        package = self.env["stock.quant.package"].create(
            {
                "name": "TEST",
                "product_packaging_id": self.product_packaging.id,
                "packaging_id": packaging.id,
            }
        )
        self.assertFalse(package.package_storage_type_id)
