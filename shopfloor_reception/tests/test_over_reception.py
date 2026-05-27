# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from .common import CommonCase


class TestOverReception(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create a picking in an assigned state for the test
        picking = cls._create_picking(
            picking_type=cls.picking_type,
            lines=[(cls.product_a, 10)],
            confirm=True,
        )
        cls.reception_picking = picking
        cls.reception_line = picking.move_line_ids[0]
        cls.menu.sudo().allow_over_reception = True

    def test_over_reception_confirmation_flow(self):
        """
        Tests the complete flow of an over-reception:
        1. User attempts to process a quantity greater than expected.
        2. The UI transitions to the `confirm_over_reception` state.
        3. The user confirms the action
        4. The action is processed and the move line is updated.
        """
        quantity_to_process = 15  # (More than expected)

        # 1. Simulate the user trying to process too much quantity
        response = self.service.process_without_pack(
            self.reception_picking.id,
            self.reception_line.id,
            quantity_to_process,
        )

        # 2. Assert the first state transition: we should be in a confirmation state
        self.assertEqual(response["next_state"], "confirm_over_reception")
        data = response["data"]
        self.assertIn("confirm_over_reception", data)
        confirm_over_reception_data = data["confirm_over_reception"]
        self.assertEqual(confirm_over_reception_data["quantity"], quantity_to_process)
        self.assertEqual(
            confirm_over_reception_data["callback"], "process_without_pack"
        )
        self.assertEqual(
            confirm_over_reception_data["picking"]["id"], self.reception_picking.id
        )

        # 3. Simulate the user confirming the over-reception
        response = self.service.process_without_pack(
            self.reception_picking.id,
            self.reception_line.id,
            confirm_over_reception_data["quantity"],
            is_over_reception_confirmed=True,
        )

        # 4. Assert the final state and data
        self.assertEqual(response["next_state"], "set_destination")
        self.assertEqual(self.reception_line.qty_done, quantity_to_process)
