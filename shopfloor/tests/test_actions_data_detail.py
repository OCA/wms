# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import io

from PIL import Image

from .test_actions_data_base import ActionsDataDetailCaseBase


def fake_colored_image(color="#4169E1", size=(800, 500)):
    with io.BytesIO() as img_file:
        Image.new("RGB", size, color).save(img_file, "JPEG")
        img_file.seek(0)
        return base64.b64encode(img_file.read())


class TestActionsDataDetailCase(ActionsDataDetailCaseBase):
    def test_data_location(self):
        location = self.stock_location
        data = self.data_detail.location_detail(location)
        self.assert_schema(self.schema_detail.location_detail(), data)
        move_lines = self.env["stock.move.line"].search(
            [
                ("location_id", "child_of", location.id),
                ("product_qty", ">", 0),
                ("state", "not in", ("done", "cancel")),
            ]
        )
        self.assertDictEqual(
            data, self._expected_location_detail(location, move_lines=move_lines)
        )

    def test_data_packaging(self):
        data = self.data_detail.packaging(self.packaging)
        self.assert_schema(self.schema_detail.packaging(), data)
        self.assertDictEqual(data, self._expected_packaging(self.packaging))

    def test_data_lot(self):
        lot = self.env["stock.production.lot"].create(
            {
                "product_id": self.product_b.id,
                "company_id": self.env.company.id,
                "ref": "#FOO",
                "removal_date": "2020-05-20",
                "expiration_date": "2020-05-31",
            }
        )
        data = self.data_detail.lot_detail(lot)
        self.assert_schema(self.schema_detail.lot_detail(), data)

        expected = {
            "id": lot.id,
            "name": lot.name,
            "ref": "#FOO",
            "product": self._expected_product_detail(self.product_b, full=True),
        }
        # ignore time and TZ, we don't care here
        self.assertEqual(data.pop("removal_date").split("T")[0], "2020-05-20")
        self.assertEqual(data.pop("expire_date").split("T")[0], "2020-05-31")
        self.assertDictEqual(data, expected)

    def test_data_package(self):
        package = self.move_a.move_line_ids.package_id
        package.packaging_id = self.packaging.id
        package.package_storage_type_id = self.storage_type_pallet
        # package.invalidate_cache()
        data = self.data_detail.package_detail(package, picking=self.picking)
        self.assert_schema(self.schema_detail.package_detail(), data)

        lines = self.env["stock.move.line"].search(
            [("package_id", "=", package.id), ("state", "not in", ("done", "cancel"))]
        )
        pickings = lines.mapped("picking_id")
        expected = {
            "id": package.id,
            "location": {
                "id": package.location_id.id,
                "name": package.location_id.display_name,
            },
            "name": package.name,
            "move_line_count": 1,
            "packaging": self.data_detail.packaging(package.packaging_id),
            "weight": 20.0,
            "pickings": self.data_detail.pickings(pickings),
            "move_lines": self.data_detail.move_lines(lines),
            "storage_type": {
                "id": self.storage_type_pallet.id,
                "name": self.storage_type_pallet.name,
            },
        }
        self.assertDictEqual(data, expected)

    def test_data_picking(self):
        picking = self.picking
        carrier = picking.carrier_id.search([], limit=1)
        picking.write(
            {
                "origin": "created by test",
                "note": "read me",
                "priority": "1",
                "carrier_id": carrier.id,
            }
        )
        picking.move_lines.write({"date": "2020-05-13"})
        data = self.data_detail.picking_detail(picking)
        self.assert_schema(self.schema_detail.picking_detail(), data)
        expected = {
            "id": picking.id,
            "move_line_count": 4,
            "package_level_count": 2,
            "bulk_line_count": 2,
            "name": picking.name,
            "note": "read me",
            "origin": "created by test",
            "ship_carrier": None,
            "weight": 110.0,
            "partner": {"id": self.customer.id, "name": self.customer.name},
            "carrier": {"id": picking.carrier_id.id, "name": picking.carrier_id.name},
            "priority": "Urgent",
            "operation_type": {
                "id": picking.picking_type_id.id,
                "name": picking.picking_type_id.name,
            },
            "move_lines": self.data_detail.move_lines(picking.move_line_ids),
            "picking_type_code": "outgoing",
        }
        self.assertEqual(data.pop("scheduled_date").split("T")[0], "2020-05-13")
        self.assertDictEqual(data, expected)

    def test_data_move_line_package(self):
        move_line = self.move_a.move_line_ids
        result_package = self.env["stock.quant.package"].create(
            {"packaging_id": self.packaging.id}
        )
        move_line.write({"qty_done": 3.0, "result_package_id": result_package.id})
        data = self.data_detail.move_line(move_line)
        self.assert_schema(self.schema_detail.move_line(), data)
        product = self.product_a.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 3.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": None,
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                "weight": 20.0,
                "storage_type": None,
            },
            "package_dest": {
                "id": result_package.id,
                "name": result_package.name,
                "move_line_count": 0,
                "weight": 6.0,
                "storage_type": None,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_lot(self):
        move_line = self.move_b.move_line_ids
        data = self.data_detail.move_line(move_line)
        self.assert_schema(self.schema_detail.move_line(), data)
        product = self.product_b.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
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
        data = self.data_detail.move_line(move_line)
        self.assert_schema(self.schema_detail.move_line(), data)
        product = self.product_c.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": {
                "id": move_line.lot_id.id,
                "name": move_line.lot_id.name,
                "ref": None,
            },
            "package_src": {
                "id": move_line.package_id.id,
                "name": move_line.package_id.name,
                "move_line_count": 1,
                "weight": 30.0,
                "storage_type": None,
            },
            "package_dest": {
                "id": move_line.result_package_id.id,
                "name": move_line.result_package_id.name,
                "move_line_count": 1,
                "weight": 0.0,
                "storage_type": None,
            },
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
        self.assertDictEqual(data, expected)

    def test_data_move_line_raw(self):
        move_line = self.move_d.move_line_ids
        data = self.data_detail.move_line(move_line)
        self.assert_schema(self.schema_detail.move_line(), data)
        product = self.product_d.with_context(location=move_line.location_id.id)
        expected = {
            "id": move_line.id,
            "qty_done": 0.0,
            "quantity": move_line.product_uom_qty,
            "product": self._expected_product_detail(product),
            "lot": None,
            "package_src": None,
            "package_dest": None,
            "location_src": self._expected_location(move_line.location_id),
            "location_dest": self._expected_location(move_line.location_dest_id),
            "priority": "1",
        }
        self.assertDictEqual(data, expected)

    def test_product(self):
        move_line = self.move_b.move_line_ids
        product = move_line.product_id.with_context(location=move_line.location_id.id)
        Partner = self.env["res.partner"].sudo()
        manuf = Partner.create({"name": "Manuf 1"})
        product.sudo().write(
            {
                "image_128": fake_colored_image(size=(128, 128)),
                "manufacturer": manuf.id,
            }
        )
        vendor_a = Partner.create({"name": "Supplier A"})
        vendor_b = Partner.create({"name": "Supplier B"})
        SupplierInfo = self.env["product.supplierinfo"].sudo()
        SupplierInfo.create(
            {
                "name": vendor_a.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUPP1",
            }
        )
        SupplierInfo.create(
            {
                "name": vendor_b.id,
                "product_tmpl_id": product.product_tmpl_id.id,
                "product_id": product.id,
                "product_code": "SUPP2",
            }
        )
        data = self.data_detail.product_detail(product)
        self.assert_schema(self.schema_detail.product_detail(), data)
        expected = self._expected_product_detail(product, full=True)
        self.assertDictEqual(data, expected)
