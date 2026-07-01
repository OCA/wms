# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import TestPackagingCommon


class TestSetPackDimension(TestPackagingCommon):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()
        cls.menu.sudo().create_new_packaging = True
        return res

    def test_create_new_packaging(self):
        response = self.service.dispatch(
            "create_new_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.line_with_packaging.id,
            },
        )

        packaging = self.env["product.packaging"].search([], order="id desc", limit=1)
        self.assertTrue(packaging)
        self._assert_response_create_new_packaging(
            response, self.picking, self.line_with_packaging, packaging
        )
