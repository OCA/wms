# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.shopfloor_reception.tests.common import CommonCase


class TestAddPackaging(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = cls._create_picking(lines=[(cls.product_a, 10)])
        cls.selected_move_line = cls.picking.move_line_ids[0]
        cls.packaging_levels = cls.env["product.packaging.level"].search([])

    def test_create_new_packaging(self):
        # select a line
        response = self.service.dispatch(
            "manual_select_move",
            params={
                "move_id": self.selected_move_line.move_id.id,
            },
        )
        self.assertEqual(response["next_state"], "set_quantity")

        # click on "create new packaging" button
        response = self.service.dispatch(
            "start_new_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
            },
        )
        self.assert_response(
            response,
            "create_new_packaging",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self.data.move_line(self.selected_move_line),
                "packaging_levels": self.data.packaging_levels(self.packaging_levels),
            },
        )

        # click on "create" button
        packaging_level = self.packaging_levels[0]
        packagings_before = self.env["product.packaging"].search([])
        response = self.service.dispatch(
            "create_new_packaging",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "name": "Test Packaging",
                "quantity": 42,
                "packaging_level_id": packaging_level.id,
            },
        )
        new_packaging = self.env["product.packaging"].search(
            [("id", "not in", packagings_before.ids)]
        )
        self.assertTrue(new_packaging)
        self.assert_response(
            response,
            "set_quantity",
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": [self.data.move_line(self.selected_move_line)],
                "confirmation_required": None,
            },
            message=self.msg_store.new_packaging_created(new_packaging),
        )
