# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataCaseBase


class ActionsDataBase(ActionsDataCaseBase):
    @classmethod
    def _set_product_lq(cls):
        limited_amount_lq = cls.env.ref(
            "l10n_eu_product_adr_dangerous_goods.limited_amount_1"
        )
        cls.product_a.is_dangerous = True
        cls.product_a.limited_amount_id = limited_amount_lq

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._set_product_lq()

    def test_data_stock_move_line(self):
        move_line = self.move_a.move_line_ids[0]
        result_package = self.env["stock.quant.package"].create(
            {"packaging_id": self.packaging.id, "pack_weight": 10}
        )
        # make weight stable
        move_line.package_id.pack_weight = 10
        move_line.write({"qty_done": 3.0, "result_package_id": result_package.id})
        package_src_data = self.data.package(
            move_line.package_id, picking=self.move_a.picking_id
        )
        self.assertTrue(package_src_data["has_lq_products"])
        package_dest_data = self.data.package(
            move_line.result_package_id, picking=self.move_a.picking_id
        )
        self.assertFalse(package_dest_data["has_lq_products"])
        expected = {
            "id": move_line.id,
            "qty_done": 3.0,
            "progress": 30.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_a),
            "lot": None,
            "package_src": package_src_data,
            "package_dest": package_dest_data,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
            "has_lq_products": True,
        }
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        for k, v in expected.items():
            self.assertEqual(data[k], v)

    def test_data_package(self):
        package = self.move_a.move_line_ids.package_id
        package.packaging_id = self.packaging.id
        package.package_storage_type_id = self.storage_type_pallet
        data = self.data.package(package, picking=self.picking, with_packaging=True)
        self.assert_schema(self.schema.package(with_packaging=True), data)
        expected = {
            "id": package.id,
            "name": package.name,
            "packaging": self._expected_packaging(package.packaging_id),
            "storage_type": self._expected_storage_type(
                package.package_storage_type_id
            ),
            "weight": 20.0,
            "has_lq_products": True,
        }
        for k, v in expected.items():
            self.assertEqual(data[k], v)
