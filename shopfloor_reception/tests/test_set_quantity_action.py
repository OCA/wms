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

    def test_cancel_action(self):
        picking = self._create_picking()
        move_product_a = picking.move_lines.filtered(
            lambda l: l.product_id == self.product_a
        )
        # User 1 and 2 selects the same picking
        service_user_1 = self.service
        service_user_1.dispatch("scan_document", params={"barcode": picking.name})
        user2 = self.shopfloor_manager
        service_user_2 = self._get_service_for_user(user2)
        response = service_user_2.dispatch(
            "scan_document", params={"barcode": picking.name}
        )
        # both users selects the same move
        service_user_1.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        move_line_user_1 = move_product_a.move_line_ids
        service_user_2.dispatch(
            "scan_line",
            params={"picking_id": picking.id, "barcode": self.product_a.barcode},
        )
        move_line_user_2 = move_product_a.move_line_ids - move_line_user_1
        # And both sets the qty done to 10
        service_user_1.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "quantity": 10,
            },
        )
        service_user_2.dispatch(
            "set_quantity",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_2.id,
                "quantity": 10,
            },
        )
        # Users are blocked, product_uom_qty is 10, but both users have qty_done=10
        # on their move line, therefore, none of them can confirm
        expected_message = {
            "body": "You cannot process that much units.",
            "message_type": "error",
        }
        response = service_user_1.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
                "quantity": 10.0,
            },
        )
        self.assertMessage(response, expected_message)
        response = service_user_2.dispatch(
            "process_with_new_pack",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_2.id,
                "quantity": 10.0,
            },
        )
        self.assertMessage(response, expected_message)
        # make user1 cancel
        service_user_1.dispatch(
            "set_quantity__cancel_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_1.id,
            },
        )
        # Since we reused the move line created by odoo for the first user, we only
        # reset the line
        self.assertTrue(move_line_user_1.exists())
        self.assertFalse(move_line_user_1.shopfloor_user_id)
        self.assertEqual(move_line_user_1.qty_done, 0)
        self.assertEqual(move_line_user_1.product_uom_qty, 10)
        # make user cancel
        service_user_2.dispatch(
            "set_quantity__cancel_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": move_line_user_2.id,
            },
        )
        # This line has been created by shopfloor, therefore, we unlinked it
        self.assertFalse(move_line_user_2.exists())
