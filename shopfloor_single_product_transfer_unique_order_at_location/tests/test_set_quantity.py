# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from odoo.addons.shopfloor_single_product_transfer.tests.common import CommonCase


class TestSingleProductTransferNoMixSetQuantity(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.location_src
        cls.picking_type.sudo().write({"same_next_picking": True})
        # Create a picking to use with the scenario
        cls.pick = cls._create_picking(lines=[(cls.product_a, 10)])
        cls._add_stock_to_product(cls.product_a, cls.location, 10)
        cls.pick.action_assign()
        # Create another picking that will be used as next picking in the chain
        cls.pick_type_out = cls.env.ref("stock.picking_type_out")
        cls.pick_next = cls._create_picking(
            picking_type=cls.pick_type_out, lines=[(cls.product_a, 3)]
        )
        cls._update_qty_in_location(cls.dispatch_location, cls.product_a, 3)
        cls.pick_next.action_confirm()
        cls.pick_next.move_lines.location_id = cls.dispatch_location
        cls.pick_next.action_assign()

    def test_set_quantity_location_empty(self):
        """Check transfer to an empty location.

        Transfer succesful.

        """
        self.pick_next.action_cancel()
        self._update_qty_in_location(self.dispatch_location, self.product_a, 0)
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product_a.barcode},
        )
        move_line = self.pick.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.name,
                "quantity": 10,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        data = {"location": self._data_for_location(self.location)}
        self.assert_response(
            response, next_state="select_product", message=expected_message, data=data
        )

    def test_set_quantity_move_at_location_same_next_picking(self):
        """Check transfer to a location with a move with same new picking.

        Transfer successful.

        """
        # Set destination move to be from the next picking
        self.pick.move_lines.move_dest_ids = [(4, self.pick_next.move_lines[0].id, 0)]
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product_a.barcode},
        )
        move_line = self.pick.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.name,
                "quantity": 10,
            },
        )
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        data = {"location": self._data_for_location(self.location)}
        self.assert_response(
            response,
            next_state="select_product",
            popup={
                "body": "Last operation of transfer {}. Next operation "
                "({}) is ready to proceed.".format(self.pick.name, self.pick_next.name)
            },
            message=expected_message,
            data=data,
        )

    def test_set_quantity_move_at_location_not_same_next_picking(self):
        """Check transfer to location with move different next picking.

        Transfer no accepted.

        """
        self.service.dispatch(
            "scan_product",
            params={"location_id": self.location.id, "barcode": self.product_a.barcode},
        )
        move_line = self.pick.move_line_ids
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "barcode": self.dispatch_location.name,
                "quantity": 10,
            },
        )
        expected_message = {"message_type": "error", "body": "You cannot place it here"}
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        self.assert_response(
            response, next_state="set_quantity", message=expected_message, data=data
        )
