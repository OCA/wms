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

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packaging = cls.env["product.packaging"].sudo().create({"name": "Pallet"})
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
        cls.picking.action_assign()

    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)

    def _expected_location(self, record, **kw):
        return {
            "id": record.id,
            "name": record.name,
            "barcode": record.barcode,
        }

    def _expected_product(self, record, **kw):
        return {
            "id": record.id,
            "name": record.name,
            "display_name": record.display_name,
            "default_code": record.default_code,
            "barcode": record.barcode,
            "packaging": [self._expected_packaging(x) for x in record.packaging_ids],
        }

    def _expected_packaging(self, record, **kw):
        return {
            "id": record.id,
            "name": record.name,
            "qty": record.qty,
        }


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
        package.product_packaging_id = self.packaging.id
        data = self.data.package(package, picking=self.picking, with_packaging=True)
        self.assert_schema(self.schema.package(with_packaging=True), data)
        expected = {
            "id": package.id,
            "name": package.name,
            "move_line_count": 1,
            "packaging": self._expected_packaging(package.product_packaging_id),
            "weight": 0.0,
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
        self.assertDictEqual(data, expected)

    def test_data_move_line_package(self):
        move_line = self.move_a.move_line_ids
        result_package = self.env["stock.quant.package"].create(
            {"product_packaging_id": self.packaging.id}
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
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "move_line_count": 0,
                # TODO
                "weight": 0.0,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
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
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "move_line_count": 1,
                # TODO
                "weight": 0,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
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
