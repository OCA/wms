# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import logging

from .common import CommonCase, PickingBatchMixin

_logger = logging.getLogger(__name__)


try:
    from cerberus import Validator
except ImportError:
    _logger.debug("Can not import cerberus")


class ActionsDataCaseBase(CommonCase):
    @classmethod
    def setUpClassVars(cls):
        super().setUpClassVars()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id
        cls.storage_type_pallet = cls.env.ref(
            "stock_storage_type.package_storage_type_pallets"
        )

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packaging_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create({"name": "Transport Box", "code": "TB", "sequence": 0})
        )
        cls.packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create({"name": "Pallet", "packaging_type_id": cls.packaging_type.id})
        )
        cls.product_b.tracking = "lot"
        cls.product_c.tracking = "lot"
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.picking.scheduled_date = "2020-08-03"
        # put product A in a package
        cls.move_a = cls.picking.move_lines[0]
        cls._fill_stock_for_moves(cls.move_a, in_package=True)
        # product B has a lot
        cls.move_b = cls.picking.move_lines[1]
        cls._fill_stock_for_moves(cls.move_b, in_lot=True)
        # product C has a lot and package
        cls.move_c = cls.picking.move_lines[2]
        cls._fill_stock_for_moves(cls.move_c, in_package=True, in_lot=True)
        # product D is raw
        cls.move_d = cls.picking.move_lines[3]
        cls._fill_stock_for_moves(cls.move_d)
        (cls.move_a + cls.move_b + cls.move_c + cls.move_d).write({"priority": "1"})
        cls.picking.action_assign()

        cls.supplier = cls.env["res.partner"].sudo().create({"name": "Supplier"})
        cls.product_a_vendor = (
            cls.env["product.supplierinfo"]
            .sudo()
            .create(
                {
                    "name": cls.supplier.id,
                    "price": 8.0,
                    "product_code": "VENDOR_CODE_A",
                    "product_id": cls.product_a.id,
                    "product_tmpl_id": cls.product_a.product_tmpl_id.id,
                }
            )
        )
        cls.product_a_variant = cls.product_a.copy(
            {
                "name": "Product A variant 1",
                "type": "product",
                "default_code": "A-VARIANT",
                "barcode": "A-VARIANT",
            }
        )
        # create another supplier info w/ lower sequence
        cls.product_a_vendor = (
            cls.env["product.supplierinfo"]
            .sudo()
            .create(
                {
                    "name": cls.supplier.id,
                    "price": 12.0,
                    "product_code": "VENDOR_CODE_VARIANT",
                    "product_id": cls.product_a_variant.id,
                    "product_tmpl_id": cls.product_a.product_tmpl_id.id,
                    "sequence": 0,
                }
            )
        )
        cls.product_a_variant.flush()
        cls.product_a_vendor.flush()

    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)

    def _expected_location(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "barcode": record.barcode,
        }
        data.update(kw)
        return data

    def _expected_product(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "display_name": record.display_name,
            "default_code": record.default_code,
            "barcode": record.barcode,
            "packaging": [
                self._expected_packaging(x) for x in record.packaging_ids if x.qty
            ],
            "uom": {
                "factor": record.uom_id.factor,
                "id": record.uom_id.id,
                "name": record.uom_id.name,
                "rounding": record.uom_id.rounding,
            },
            "supplier_code": self._expected_supplier_code(record),
        }
        data.update(kw)
        return data

    def _expected_supplier_code(self, product):
        supplier_info = product.seller_ids.filtered(lambda x: x.product_id == product)
        return supplier_info[0].product_code if supplier_info else ""

    def _expected_packaging(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.packaging_type_id.name,
            "code": record.packaging_type_id.code,
            "qty": record.qty,
        }
        data.update(kw)
        return data

    def _expected_storage_type(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
        }
        data.update(kw)
        return data

    def _expected_package(self, record, **kw):
        data = {
            "id": record.id,
            "name": record.name,
            "weight": record.pack_weight,
            "storage_type": None,
        }
        data.update(kw)
        return data


class ActionsDataCase(ActionsDataCaseBase):
    def test_data_packaging(self):
        data = self.data.packaging(self.packaging)
        self.assert_schema(self.schema.packaging(), data)
        self.assertDictEqual(data, self._expected_packaging(self.packaging))

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
        expected = {"id": lot.id, "name": lot.name, "ref": "#FOO"}
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
            "move_line_count": 1,
            "packaging": self._expected_packaging(package.packaging_id),
            "storage_type": self._expected_storage_type(
                package.package_storage_type_id
            ),
            "weight": 0.0,
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
        self.picking.write({"origin": "created by test", "note": "read me"})
        data = self.data.picking(self.picking)
        self.assert_schema(self.schema.picking(), data)
        expected = {
            "id": self.picking.id,
            "move_line_count": 4,
            "name": self.picking.name,
            "note": "read me",
            "origin": "created by test",
            "weight": 110.0,
            "partner": {"id": self.customer.id, "name": self.customer.name},
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
        expected = {
            "id": move_line.id,
            "qty_done": 3.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_a),
            "lot": None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                # TODO
                "weight": 0.0,
                "storage_type": None,
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "move_line_count": 0,
                # TODO
                "weight": 0.0,
                "storage_type": None,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
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
            },
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_package_lot(self):
        move_line = self.move_c.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product(self.product_c),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
            },
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                # TODO
                "weight": 0,
                "storage_type": None,
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "move_line_count": 1,
                # TODO
                "weight": 0,
                "storage_type": None,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
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
