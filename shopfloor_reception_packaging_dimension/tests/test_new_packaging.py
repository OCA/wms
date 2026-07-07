# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import TestPackagingCommon


class TestNewPackaging(TestPackagingCommon):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()
        cls.menu.sudo().create_new_packaging = True
        return res

    def test_new_packaging(self):
        # Create the new packaging
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

        # Cancel the action (delete the created packaging)
        message = self.msg_store.packaging_deleted(packaging)
        response = self.service.dispatch(
            "delete_new_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.line_with_packaging.id,
                "packaging_id": packaging.id,
            },
        )
        self.assertFalse(packaging.exists())
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": [self.data.move_line(self.line_with_packaging)],
                "confirmation_required": None,
                "create_new_packaging": True,
            },
            message=message,
        )
