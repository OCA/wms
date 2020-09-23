# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
from odoo.exceptions import ValidationError

from .common import TestStorageTypeCommon


class TestStorageTypeMove(TestStorageTypeCommon):
    def test_package_storage_type_height_required(self):
        packaging = self.product_lot_pallets_product_packaging
        storage_type = packaging.package_storage_type_id
        # Without 'height_required'
        self.env["stock.quant.package"].create(
            {"name": "TEST1", "product_packaging_id": packaging.id}
        )
        # With 'height_required'
        storage_type.height_required = True
        with self.assertRaises(ValidationError):
            self.env["stock.quant.package"].create(
                {"name": "TEST2", "product_packaging_id": packaging.id}
            )
