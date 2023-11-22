# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetLotConfirm(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.tracking = "lot"

    def test_ensure_expiry_date(self):
        picking = self._create_picking()
        self.product_a.use_expiration_date = True
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        # product has been set as requiring a expiration date.
        # Trying to move to the next screen should return an error
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
            message={"message_type": "error", "body": "Missing expiration date."},
        )
        # Now, set the expiry date
        expiration_date = "2022-08-24 12:00:00"
        self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "expiration_date": expiration_date,
            },
        )
        # And try to confirm again
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
            },
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )
