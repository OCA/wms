# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_actions_data_base import ActionsDataDetailManufCaseBase


class TestActionsDataDetailManufCase(ActionsDataDetailManufCaseBase):
    def test_product(self):
        move_line = self.move_b.move_line_ids
        product = move_line.product_id.with_context(location=move_line.location_id.id)
        Partner = self.env["res.partner"].sudo()
        manuf = Partner.create({"name": "Manuf 1"})
        product.sudo().write(
            {
                "manufacturer_id": manuf.id,
            }
        )
        data = self.data_detail.product_detail(product)
        self.assert_schema(self.schema_detail.product_detail(), data)
        expected = self._expected_product_detail(product, full=True)
        self.assertDictEqual(data, expected)
