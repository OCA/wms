# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2025 ACSONE SA/NV (https://acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
import base64
import io

from PIL import Image

from odoo.addons.shopfloor.tests.test_actions_data_base import ActionsDataDetailCaseBase


def fake_colored_image(color="#4169E1", size=(800, 500)):
    with io.BytesIO() as img_file:
        Image.new("RGB", size, color).save(img_file, "JPEG")
        img_file.seek(0)
        return base64.b64encode(img_file.read())


class TestActionsDataDetailCase(ActionsDataDetailCaseBase):
    def _expected_product_detail(self, record, **kw):
        res = super()._expected_product_detail(record, **kw)
        res.update(
            {
                "length": record.product_length,
                "width": record.product_width,
                "height": record.product_height,
                "weight": record.weight,
                "dimension_uom": {
                    "id": record.dimensional_uom_id.id,
                    "factor": record.dimensional_uom_id.factor,
                    "name": record.dimensional_uom_id.name,
                    "rounding": record.dimensional_uom_id.rounding,
                },
                "weight_uom": {
                    "id": record.weight_uom_id.id,
                    "factor": record.weight_uom_id.factor,
                    "name": record.weight_uom_id.name,
                    "rounding": record.weight_uom_id.rounding,
                },
            }
        )

        return res

    def test_product(self):
        move_line = self.move_b.move_line_ids
        product = move_line.product_id.with_context(location=move_line.location_id.id)
        Partner = self.env["res.partner"].sudo()

        vendor_a = Partner.create({"name": "Supplier A"})
        vendor_b = Partner.create({"name": "Supplier B"})
        SupplierInfo = self.env["product.supplierinfo"].sudo()
        SupplierInfo.create(
            {
                "partner_id": vendor_a.id,
                "product_id": product.id,
                "product_code": "SUPP1",
            }
        )
        SupplierInfo.create(
            {
                "partner_id": vendor_b.id,
                "product_id": product.id,
                "product_code": "SUPP2",
            }
        )
        product.sudo().write(
            {
                "product_length": 12.5,
                "product_height": 10.1,
                "product_width": 3.5,
                "weight": 2.6,
            }
        )
        data = self.data_detail.product_detail(product)
        self.assert_schema(self.schema_detail.product_detail(), data)
        expected = self._expected_product_detail(product, full=True)
        self.assertDictEqual(data, expected)

    def test_product_template(self):
        # Check product supplierinfo on template level
        move_line = self.move_b.move_line_ids
        product = move_line.product_id.with_context(location=move_line.location_id.id)
        Partner = self.env["res.partner"].sudo()
        manuf = Partner.create({"name": "Manuf 1"})
        product.sudo().write(
            {
                "image_128": fake_colored_image(size=(128, 128)),
                "manufacturer_id": manuf.id,
            }
        )
        vendor_a = Partner.create({"name": "Supplier A"})
        vendor_b = Partner.create({"name": "Supplier B"})
        SupplierInfo = self.env["product.supplierinfo"].sudo()
        SupplierInfo.create(
            {
                "partner_id": vendor_a.id,
                "product_id": product.id,
                "product_code": "SUPP1",
            }
        )
        SupplierInfo.create(
            {
                "partner_id": vendor_b.id,
                "product_id": product.id,
                "product_code": "SUPP2",
            }
        )
        data = self.data_detail.product_detail(product)
        self.assert_schema(self.schema_detail.product_detail(), data)
        expected = self._expected_product_detail(product, full=True)
        self.assertDictEqual(data, expected)
