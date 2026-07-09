# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import Command

from odoo.addons.shopfloor_reception.tests.common import CommonCase


# pylint: disable=W8110
class TestPackagingCommon(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10), (cls.product_c, 10)]
        )
        cls.default_packaging_level = cls.env[
            "product.packaging"
        ].default_packaging_level_id()
        cls.default_packaging_level.sudo().write(
            {
                "shopfloor_collect_length": True,
                "shopfloor_collect_width": True,
                "shopfloor_collect_height": True,
                "shopfloor_collect_weight": True,
                "shopfloor_collect_barcode": True,
            }
        )
        # Picking has 3 products
        # Product A with one packaging
        # Product B with no packaging
        cls.product_b.packaging_ids = [Command.clear()]
        # Product C with 2 packaging
        cls.product_c_packaging_2 = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Big Box",
                    "product_id": cls.product_c.id,
                    "barcode": "ProductCBigBox",
                    "qty": 6,
                }
            )
        )

        cls.line_with_packaging = cls.picking.move_line_ids[0]
        cls.line_without_packaging = cls.picking.move_line_ids[1]

    def _assert_response_set_dimension(
        self, response, picking, line, packaging, message=None
    ):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_line(line),
            "packaging": self.data.packaging_dimensions(packaging),
        }
        self.assert_response(
            response,
            next_state="set_packaging_dimension",
            data=data,
            message=message,
        )

    def _assert_response_create_new_packaging(self, response, picking, line, packaging):
        data = {
            "picking": self.data.picking(picking),
            "selected_move_line": self.data.move_line(line),
            "packaging": self.data.packaging_dimensions(packaging),
        }
        self.assert_response(
            response,
            next_state="create_new_packaging",
            data=data,
            message=self.msg_store.new_packaging_created(packaging),
        )
