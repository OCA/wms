# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetQuantityAction(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking()
        cls.selected_move_line = cls.picking.move_line_ids.filtered(
            lambda l: l.product_id == cls.product_a
        )

    def test_process_with_existing_package(self):
        response = self.service.dispatch(
            "process_with_existing_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_move_line.ids,
            },
        )
        data = self.data.picking(self.picking)
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(self.selected_move_line),
            },
        )

    def test_process_with_new_package(self):
        response = self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_move_line.ids,
            },
        )
        data = self.data.picking(self.picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(self.selected_move_line),
            },
        )
        self.assertTrue(self.selected_move_line.result_package_id)

    def test_process_without_package(self):
        response = self.service.dispatch(
            "process_without_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_move_line.ids,
            },
        )
        data = self.data.picking(self.picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_lines": self.data.move_lines(self.selected_move_line),
            },
        )
        self.assertFalse(self.selected_move_line.result_package_id)
