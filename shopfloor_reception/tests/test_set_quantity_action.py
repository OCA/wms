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
        package = self.env["stock.quant.package"].create(
            {
                "name": "FOO",
                "packaging_id": self.product_a_packaging.id,
            }
        )
        self.selected_move_line.result_package_id = package
        response = self.service.dispatch(
            "process_with_existing_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        picking_data = self.data.picking(self.picking)
        package_data = self.data.packages(
            package.with_context(picking_id=self.picking.id),
            picking=self.picking,
            with_packaging=True,
        )
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": picking_data,
                "packages": package_data,
                "selected_move_line": self.data.move_lines(self.selected_move_line),
            },
        )

    def test_process_with_new_package(self):
        response = self.service.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        data = self.data.picking(self.picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(self.selected_move_line),
            },
        )
        self.assertTrue(self.selected_move_line.result_package_id)

    def test_process_without_package(self):
        response = self.service.dispatch(
            "process_without_pack",
            params={
                "picking_id": self.picking.id,
                "selected_line_id": self.selected_move_line.id,
                "quantity": 2,
            },
        )
        data = self.data.picking(self.picking)
        self.assert_response(
            response,
            next_state="set_destination",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(self.selected_move_line),
            },
        )
        self.assertFalse(self.selected_move_line.result_package_id)
