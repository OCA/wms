# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestSetLot(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_a.tracking = "lot"

    def test_set_existing_lot(self):
        picking = self._create_picking()
        lot = self._create_lot()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        self.assertEqual(selected_move_line.lot_id, lot)
        self.assertFalse(selected_move_line.expiration_date)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_set_new_lot_on_line_with_lot(self):
        picking = self._create_picking()
        lot_before = self._create_lot()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        selected_move_line.lot_id = lot_before
        lot_after = self._create_lot()
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot_after.name,
            },
        )
        self.assertEqual(selected_move_line.lot_id, lot_after)
        self.assertFalse(selected_move_line.expiration_date)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_set_existing_lot_with_expiration_date(self):
        self.product_a.use_expiration_date = True
        picking = self._create_picking()
        expiration_date = "2022-08-23 12:00:00"
        lot = self._create_lot(expiration_date=expiration_date)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        self.assertEqual(str(selected_move_line.expiration_date), expiration_date)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_set_new_lot(self):
        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": "FooBar",
            },
        )
        self.assertEqual(selected_move_line.lot_id.name, "FooBar")
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )

    def test_set_expiry_date(self):
        # First, set the lot
        picking = self._create_picking()
        lot = self._create_lot()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        # Then, set the expiration date
        expiration_date = "2022-08-24 12:00:00"
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "expiration_date": expiration_date,
            },
        )
        self.assertEqual(str(lot.expiration_date), expiration_date)
        self.assertEqual(str(selected_move_line.expiration_date), expiration_date)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(selected_move_line),
            },
        )
