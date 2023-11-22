# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import PickingBatchMixin
from .test_actions_data_base import ActionsDataCaseBase


class ActionsDataCase(ActionsDataCaseBase):
    def test_data_packaging(self):
        data = self.data.packaging(self.packaging)
        self.assert_schema(self.schema.packaging(), data)
        self.assertDictEqual(data, self._expected_packaging(self.packaging))

    def test_data_delivery_packaging(self):
        data = self.data.delivery_packaging(self.delivery_packaging)
        self.assert_schema(self.schema.delivery_packaging(), data)
        self.assertDictEqual(
            data, self._expected_delivery_packaging(self.delivery_packaging)
        )

    def test_data_location(self):
        location = self.stock_location
        data = self.data.location(location)
        self.assert_schema(self.schema.location(), data)
        expected = {
            "id": location.id,
            "name": location.name,
            "barcode": location.barcode,
        }
        self.assertDictEqual(data, expected)

    def test_data_location_no_barcode(self):
        location = self.stock_location
        location.sudo().barcode = None
        data = self.data.location(location)
        self.assert_schema(self.schema.location(), data)
        expected = {
            "id": location.id,
            "name": location.name,
            "barcode": location.name,
        }
        self.assertDictEqual(data, expected)

    def test_data_location_with_operation_progress(self):
        location = self.stock_location
        location.sudo().barcode = None
        data = self.data.location(location, with_operation_progress=True)
        self.assert_schema(self.schema.location(), data)
        expected = {
            "id": location.id,
            "name": location.name,
            "barcode": location.name,
            "operation_progress": {
                "done": 16.0,
                "to_do": 165.0,
            },
        }
        self.assertDictEqual(data, expected)

    def test_data_lot(self):
        lot = self.env["stock.production.lot"].create(
            {
                "product_id": self.product_b.id,
                "company_id": self.env.company.id,
                "ref": "#FOO",
            }
        )
        data = self.data.lot(lot)
        self.assert_schema(self.schema.lot(), data)
        expected = {
            "id": lot.id,
            "name": lot.name,
            "ref": "#FOO",
            "expiration_date": None,
        }
        self.assertDictEqual(data, expected)

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
            "total_quantity": 10.0,
            "weight": 20.0,
        }
        self.assertDictEqual(data, expected)

    def test_data_package_with_move_line_count(self):
        package = self.move_a.move_line_ids.package_id
        package.packaging_id = self.packaging.id
        package.package_storage_type_id = self.storage_type_pallet
        data = self.data.package(
            package,
            picking=self.picking,
            with_packaging=True,
            with_package_move_line_count=True,
        )
        self.assert_schema(self.schema.package(with_packaging=True), data)
        expected = {
            "id": package.id,
            "name": package.name,
            "move_line_count": 2,
            "packaging": self._expected_packaging(package.packaging_id),
            "storage_type": self._expected_storage_type(
                package.package_storage_type_id
            ),
            "weight": 20.0,
            "total_quantity": sum(package.quant_ids.mapped("quantity")),
        }
        self.assertDictEqual(data, expected)

    def test_data_package_level(self):
        package_level = self.picking.package_level_ids[0]
        data = self.data.package_level(package_level)
        self.assert_schema(self.schema.package_level(), data)
        expected = {
            "id": package_level.id,
            "is_done": False,
            "picking": self.picking.jsonify(["id", "name"])[0],
            "package_src": self._expected_package(package_level.package_id),
            "location_dest": self._expected_location(package_level.location_dest_id),
            "location_src": self._expected_location(
                package_level.picking_id.location_id
            ),
            "product": self._expected_product(
                package_level.package_id.single_product_id
            ),
            "quantity": package_level.package_id.single_product_qty,
        }
        self.assertDictEqual(data, expected)

    def test_data_picking(self):
        carrier = self.picking.carrier_id.search([], limit=1)
        self.picking.write(
            {"origin": "created by test", "note": "read me", "carrier_id": carrier.id}
        )
        data = self.data.picking(self.picking)
        self.assert_schema(self.schema.picking(), data)
        expected = {
            "id": self.picking.id,
            "move_line_count": 4,
            "package_level_count": 2,
            "bulk_line_count": 2,
            "name": self.picking.name,
            "note": "read me",
            "origin": "created by test",
            "weight": 110.0,
            "partner": {"id": self.customer.id, "name": self.customer.name},
            "carrier": {"id": carrier.id, "name": carrier.name},
            "ship_carrier": None,
            "priority": "0",
        }
        self.assertEqual(data.pop("scheduled_date").split("T")[0], "2020-08-03")
        self.assertDictEqual(data, expected)

    def test_data_picking_with_progress(self):
        carrier = self.picking.carrier_id.search([], limit=1)
        self.picking.write(
            {"origin": "created by test", "note": "read me", "carrier_id": carrier.id}
        )
        data = self.data.picking(self.picking, with_progress=True)
        self.assert_schema(self.schema.picking(), data)
        expected = {
            "id": self.picking.id,
            "move_line_count": 4,
            "package_level_count": 2,
            "bulk_line_count": 2,
            "name": self.picking.name,
            "note": "read me",
            "origin": "created by test",
            "weight": 110.0,
            "partner": {"id": self.customer.id, "name": self.customer.name},
            "carrier": {"id": carrier.id, "name": carrier.name},
            "ship_carrier": None,
            "progress": 0.0,
            "priority": "0",
        }
        self.assertEqual(data.pop("scheduled_date").split("T")[0], "2020-08-03")
        self.assertDictEqual(data, expected)

    def test_data_product(self):
        (
            self.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box 2",
                    "product_id": self.product_a.id,
                    "barcode": "ProductABox2",
                }
            )
        )
        self.product_a.packaging_ids.write({"qty": 0})
        data = self.data.product(self.product_a)
        self.assert_schema(self.schema.product(), data)
        # No packaging expected as all qties are zero
        expected = self._expected_product(self.product_a)
        self.assertDictEqual(data, expected)
        # packaging w/ no zero qty are included
        self.product_a.packaging_ids[0].write({"qty": 100})
        self.product_a.packaging_ids[1].write({"qty": 20})
        data = self.data.product(self.product_a)
        expected = self._expected_product(self.product_a)
        self.assertDictEqual(data, expected)

    def test_data_move_line_package(self):
        move_line = self.move_a.move_line_ids
        result_package = self.env["stock.quant.package"].create(
            {"packaging_id": self.packaging.id}
        )
        move_line.write({"qty_done": 3.0, "result_package_id": result_package.id})
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        self.assertIn(self.move_a.state, ["partially_available", "assigned", "done"])
        expected = {
            "id": move_line.id,
            "qty_done": 3.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_a),
            "lot": None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "weight": 20.0,
                "storage_type": None,
                "total_quantity": sum(
                    move_line.package_id.quant_ids.mapped("quantity")
                ),
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "weight": 6.0,
                "storage_type": None,
                "total_quantity": sum(result_package.quant_ids.mapped("quantity")),
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
            "progress": 30.0,
        }
        self.assertDictEqual(data, expected)
        data = self.data.move_line(move_line, with_package_move_line_count=True)
        expected["package_src"]["move_line_count"] = 1
        expected["package_dest"]["move_line_count"] = 1
        self.assertDictEqual(data, expected)

    def test_data_move_line_lot(self):
        move_line = self.move_b.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_b),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
                "expiration_date": None,
            },
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
            "progress": 0.0,
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_package_lot(self):
        move_line = self.move_c.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        self.assertIn(self.move_a.state, ["partially_available", "assigned", "done"])
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_c),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
                "expiration_date": None,
            },
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "weight": 30,
                "storage_type": None,
                "total_quantity": sum(
                    move_line.package_id.quant_ids.mapped("quantity")
                ),
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "weight": 0,
                "storage_type": None,
                "total_quantity": sum(
                    move_line.result_package_id.quant_ids.mapped("quantity")
                ),
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
            "progress": 0.0,
        }
        self.assertDictEqual(data, expected)
        data = self.data.move_line(move_line, with_package_move_line_count=True)
        self.assert_schema(self.schema.move_line(), data)
        expected["package_src"]["move_line_count"] = 2
        expected["package_dest"]["move_line_count"] = 2
        self.assertDictEqual(data, expected)

    def test_data_move_line_raw(self):
        move_line = self.move_d.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_d),
            "lot": None,
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
            "progress": 0.0,
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_with_picking(self):
        move_line = self.move_d.move_line_ids
        data = self.data.move_line(move_line, with_picking=True)
        self.assert_schema(self.schema.move_line(with_picking=True), data)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_d),
            "lot": None,
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "picking": self.data.picking(move_line.picking_id),
            "priority": "1",
            "progress": 0.0,
        }
        self.assertDictEqual(data, expected)


class ActionsDataCaseBatchPicking(ActionsDataCaseBase, PickingBatchMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=20),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=30)],
            ]
        )

    def test_data_picking_batch(self):
        data = self.data.picking_batch(self.batch)
        self.assert_schema(self.schema.picking_batch(), data)
        # no assigned pickings
        expected = {
            "id": self.batch.id,
            "name": self.batch.name,
            "picking_count": 0,
            "move_line_count": 0,
            "weight": 0.0,
        }
        self.assertDictEqual(data, expected)

        self._simulate_batch_selected(self.batch, fill_stock=True)
        expected.update(
            {
                "picking_count": 2,
                "move_line_count": 3,
                "weight": sum(self.batch.picking_ids.mapped("total_weight")),
            }
        )
        data = self.data.picking_batch(self.batch)
        self.assertDictEqual(data, expected)

    def test_data_picking_batch_with_pickings(self):
        self._simulate_batch_selected(self.batch, fill_stock=True)
        data = self.data.picking_batch(self.batch, with_pickings=True)
        self.assert_schema(self.schema.picking_batch(with_pickings=True), data)
        # no assigned pickings
        expected = {
            "id": self.batch.id,
            "name": self.batch.name,
            "picking_count": 2,
            "move_line_count": 3,
            "weight": sum(self.batch.picking_ids.mapped("total_weight")),
            "pickings": self.data.pickings(self.batch.picking_ids),
        }
        self.assertDictEqual(data, expected)
