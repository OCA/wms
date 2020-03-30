import logging

from .common import CommonCase

_logger = logging.getLogger(__name__)


try:
    from cerberus import Validator
except ImportError:
    _logger.debug("Can not import cerberus")


class ActionsDataCase(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.wh = cls.env.ref("stock.warehouse0")
        cls.picking_type = cls.wh.out_type_id
        cls.packaging = cls.env["product.packaging"].create({"name": "Pallet"})
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

    def setUp(self):
        super().setUp()
        with self.work_on_actions() as work:
            self.data = work.component(usage="data")
        with self.work_on_services() as work:
            self.schema = work.component(usage="schema")

    def assert_schema(self, schema, data):
        validator = Validator(schema)
        self.assertTrue(validator.validate(data), validator.errors)

    def test_data_packaging(self):
        data = self.data.packaging(self.packaging)
        self.assert_schema(self.schema.packaging(), data)
        expected = {"id": self.packaging.id, "name": self.packaging.name}
        self.assertDictEqual(data, expected)

    def test_data_location(self):
        location = self.stock_location
        data = self.data.location(location)
        self.assert_schema(self.schema.location(), data)
        expected = {"id": location.id, "name": location.name}
        self.assertDictEqual(data, expected)

    def test_data_lot(self):
        lot = self.env["stock.production.lot"].create(
            {"product_id": self.product_b.id, "company_id": self.env.company.id}
        )
        data = self.data.lot(lot)
        self.assert_schema(self.schema.lot(), data)
        expected = {"id": lot.id, "name": lot.name}
        self.assertDictEqual(data, expected)

    def test_data_package(self):
        package = self.move_a.move_line_ids.package_id
        package.product_packaging_id = self.packaging.id
        data = self.data.package(package, picking=self.picking)
        self.assert_schema(self.schema.package(), data)
        expected = {
            "id": package.id,
            "name": package.name,
            "line_count": 1,
            "packaging_name": self.packaging.name,
            # TODO
            "weight": 0,
        }
        self.assertDictEqual(data, expected)

    def test_data_picking_summary(self):
        self.picking.write({"origin": "created by test", "note": "read me"})
        data = self.data.picking_summary(self.picking)
        self.assert_schema(self.schema.picking(), data)
        expected = {
            "id": self.picking.id,
            "line_count": 4,
            "name": self.picking.name,
            "note": "read me",
            "origin": "created by test",
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
            "product": {
                "id": self.product_a.id,
                "name": "Product A",
                "display_name": "[A] Product A",
                "default_code": "A",
            },
            "lot": None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "line_count": 1,
                "packaging_name": "",
                # TODO
                "weight": 0,
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "line_count": 0,
                "packaging_name": self.packaging.name,
                # TODO
                "weight": 0,
            },
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "location_dest": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
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
            "product": {
                "id": self.product_b.id,
                "name": "Product B",
                "display_name": "[B] Product B",
                "default_code": "B",
            },
            "lot": {"id": move_line.lot_id.id, "name": move_line.lot_id.name},
            "package_src": None,
            "package_dest": None,
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "location_dest": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_package_lot(self):
        self.maxDiff = None
        move_line = self.move_c.move_line_ids
        data = self.data.move_line(move_line)
        self.assert_schema(self.schema.move_line(), data)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": {
                "id": self.product_c.id,
                "name": "Product C",
                "display_name": "[C] Product C",
                "default_code": "C",
            },
            "lot": {"id": move_line.lot_id.id, "name": move_line.lot_id.name},
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "line_count": 1,
                "packaging_name": "",
                # TODO
                "weight": 0,
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "line_count": 1,
                "packaging_name": "",
                # TODO
                "weight": 0,
            },
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "location_dest": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
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
            "product": {
                "id": self.product_d.id,
                "name": "Product D",
                "display_name": "[D] Product D",
                "default_code": "D",
            },
            "lot": None,
            "package_src": None,
            "package_dest": None,
            "location_src": {
                "id": move_line.location_id.id,
                "name": move_line.location_id.name,
            },
            "location_dest": {
                "id": move_line.location_dest_id.id,
                "name": move_line.location_dest_id.name,
            },
        }
        self.assertDictEqual(data, expected)
