# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)
# pylint: disable=missing-return
from unittest import mock

from odoo import fields

from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult
from odoo.addons.shopfloor.actions.search import SearchAction, SearchResult

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
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
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
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
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
                "expiration_date": expiration_date,
            },
        )
        self.assertEqual(str(selected_move_line.expiration_date), expiration_date)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
            },
            message={
                "body": "The selected expiration date is in the past. Are you "
                "sure you want to continue?",
                "message_type": "warning",
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
        self.assertEqual(selected_move_line.lot_name, "FooBar")
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
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
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "expiration_date": self._date_as_input_date("2022-08-24"),
            },
        )
        self.assertEqual(
            selected_move_line.expiration_date,
            fields.Datetime.to_datetime("2022-08-24"),
        )
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
            },
        )

    def test_set_lot_expiration_find_date(self):
        # Check if we start by entering a date, and a lot
        # already exists with that date, it is used
        picking = self._create_picking()
        self.product_a.use_expiration_date = True
        lot = self._create_lot()
        expiration_date = fields.Datetime.from_string("2222-07-02")
        lot.expiration_date = expiration_date
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "expiration_date": self._date_as_input_date("2222-07-02"),
            },
        )

        message_reponse = response.get("message")
        self.assertIsNone(message_reponse)
        self.assertEqual(selected_move_line.lot_id, lot)
        data = response.get("data").get("set_lot").get("selected_move_line")
        data = data and data[0] or {}
        self.assertEqual(data["lot_name"], lot.name)
        self.assertEqual(data["expiration_date"], "2222-07-02T00:00:00")

    def test_set_lot_expiration_from_parse(self):
        # Check if lot scanned contains expiration
        # date information

        picking = self._create_picking()
        self.product_a.use_expiration_date = True
        lot = self._create_lot()
        expiration_date = fields.Datetime.from_string("2222-07-02")
        lot.expiration_date = expiration_date
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = SearchResult(
                record=lot,
                type="lot",
                parse_result=[
                    BarcodeResult(type="lot", value=lot.name),
                    BarcodeResult(
                        type="expiration_date",
                        value=self._date_as_input_date(expiration_date),
                    ),
                ],
            )
            response = self.service.dispatch(
                "set_lot",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "lot_name": lot.name,
                },
            )
        message_reponse = response.get("message")
        self.assertIsNone(message_reponse)

        self.assertEqual(selected_move_line.expiration_date, expiration_date)

    def test_set_lot_no_expiration(self):
        # Check if message that requires expiration date
        # is raised
        picking = self._create_picking()
        lot = self._create_lot()
        lot.expiration_date = False
        self.product_a.use_expiration_date = True
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
        message_reponse = response.get("message")
        self.assertEqual("error", message_reponse.get("message_type"))
        self.assertEqual("Missing expiration date.", message_reponse.get("body"))

        # if the selected lot has an expiration date, it should be used
        expiration_date = lot.expiration_date = fields.Datetime.from_string(
            "2220-07-02"
        )
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        self.assertEqual(lot.expiration_date, expiration_date)
        self.assertEqual(selected_move_line.expiration_date, expiration_date)
        self.assertEqual(selected_move_line.lot_id, lot)
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, lot_name=True, expiration_date=True
                ),
            },
        )

    def test_set_lot_messages(self):
        # Check if message that requires expiration date
        # is raised
        picking = self._create_picking()
        lot = self._create_lot()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid
        selected_move_line.qty_done = selected_move_line.reserved_uom_qty
        selected_move_line.lot_id = lot
        picking._action_done()
        response = self.service.dispatch(
            "set_lot",
            params={
                "picking_id": picking.id,
                "selected_line_id": selected_move_line.id,
                "lot_name": lot.name,
            },
        )
        message_reponse = response.get("message")
        self.assertEqual("info", message_reponse.get("message_type"))
        self.assertEqual("Operation already processed.", message_reponse.get("body"))
