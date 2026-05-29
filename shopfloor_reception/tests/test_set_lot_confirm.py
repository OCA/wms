# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from freezegun import freeze_time

from .common import CommonCase


class TestSetLotConfirm(CommonCase):
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
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        self.assertEqual(selected_move_line.lot_id, lot)
        self.assertFalse(selected_move_line.expiration_date)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    def test_set_new_lot(self):
        picking = self._create_picking()
        picking.picking_type_id.sudo().use_create_lots = True
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": "FooBar",
            },
        )
        self.assertEqual(selected_move_line.lot_id.name, "FooBar")
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
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
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot_after.name,
            },
        )
        self.assertEqual(selected_move_line.lot_id, lot_after)
        self.assertFalse(selected_move_line.expiration_date)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    @freeze_time("2020-01-01 11:00:00")
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
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        self.assertEqual(str(selected_move_line.expiration_date), expiration_date)
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    @freeze_time("2020-01-01 11:00:00")
    def test_set_existing_lot_try_overwrite_expiration_date_error(self):
        self.product_a.use_expiration_date = True
        picking = self._create_picking()
        lot_expiration_date = "2022-08-23 12:00:00"
        lot = self._create_lot(expiration_date=lot_expiration_date)
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid

        new_expiration_date = "2022-08-27 12:00:00"
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
                "expiration_date": new_expiration_date,
            },
        )
        self.assertEqual(
            str(lot.expiration_date),
            lot_expiration_date,
            "Existing lot expiration date should not be overwritten",
        )

        # The error should send back the selected lot name and expiration date so
        # to prevent clearing the UI fields after error message
        move_line_response_data = self.data.move_lines(selected_move_line)
        move_line_response_data[0]["lot"] = {
            "name": lot.name,
            "expiration_date": new_expiration_date.replace(" ", "T"),
        }
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": move_line_response_data,
            },
            message=self.msg_store.lot_already_exists_different_expiration_date(lot),
        )

    @freeze_time("2020-01-01 11:00:00")
    def test_set_new_lot_and_expiration_date(self):
        picking = self._create_picking()
        picking.picking_type_id.sudo().use_create_lots = True
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": "FooBar",
                "expiration_date": "2022-08-24 12:00:00",
            },
        )
        self.assertEqual(selected_move_line.lot_id.name, "FooBar")
        self.assertEqual(
            str(selected_move_line.lot_id.expiration_date), "2022-08-24 12:00:00"
        )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self.data.move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )

    @freeze_time("2020-01-01 11:00:00")
    def test_ensure_expiry_date(self):
        picking = self._create_picking()
        self.product_a.use_expiration_date = True
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        # product has been set as requiring a expiration date.
        # Trying to move to the next screen should return an error
        lot_name = "Test Lot"
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot_name,
            },
        )

        excepted_selected_move_line_data = self.data.move_lines(selected_move_line)
        # The expected response should contain the lot name even if the lot is
        # not defined on the move line already
        excepted_selected_move_line_data[0]["lot"] = {"name": lot_name}

        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": excepted_selected_move_line_data,
            },
            message=self.msg_store.expiration_date_missing(),
        )
        self.assertEqual(
            len(self.env["stock.lot"].search([("name", "=", lot_name)])),
            0,
            "No new lot should have been created in case of error.",
        )

    def test_set_new_lot_creation_disabled_error(self):
        picking = self._create_picking()
        picking.picking_type_id.sudo().use_create_lots = False

        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid

        lot_name = "NewForbiddenLot"

        nb_lots_before = self.env["stock.lot"].search_count([("name", "=", lot_name)])
        response = self.service.dispatch(
            "set_lot_confirm_action",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot_name,
            },
        )

        # The response should keep us on 'set_lot' and show the error message
        expected_selected_move_line_data = self.data.move_lines(selected_move_line)
        expected_selected_move_line_data[0]["lot"] = {"name": lot_name}

        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": expected_selected_move_line_data,
            },
            message=self.msg_store.lot_creation_disabled(picking.picking_type_id),
        )

        nb_lots_after = self.env["stock.lot"].search_count([("name", "=", lot_name)])
        self.assertEqual(nb_lots_after, nb_lots_before)
