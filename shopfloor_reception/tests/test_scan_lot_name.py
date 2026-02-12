# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import timedelta
from unittest import mock

from odoo import fields

from odoo.addons.shopfloor.actions.barcode_parser import BarcodeResult
from odoo.addons.shopfloor.actions.search import SearchAction, SearchResult

from .common import CommonCase


class TestScanLotName(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()
        cls.product_a.tracking = "lot"
        return res

    def test_scan_lot_name_extract_expiration_date_new_lot(self):
        """
        Test that the expiration date can be extracted from barcode scan
        (case when the lot does not already exsit in db)
        """
        picking = self._create_picking()
        lot = self._create_lot()
        expiration_date = fields.Datetime.from_string("2022-07-02")
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid

        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = SearchResult(
                record=None,
                type="None",
                parse_result=[
                    BarcodeResult(type="unknown", value=lot.name),
                    BarcodeResult(type="expiration_date", value=expiration_date),
                ],
            )
            res = self.service.dispatch(
                "scan_lot_name",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "lot_name": lot.name,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            expiration_date.isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"], lot.name
        )

    def test_scan_lot_name_extract_expiration_date_existing_lot(self):
        """
        When lot already exists, take the expiration date from the existing lot.

        Ensure there is a warning in case of mismatch between expiration date found in
        the barcode and the one on the existing lot.
        """
        picking = self._create_picking()

        expiration_date = fields.Datetime.from_string("2022-07-02")
        lot = self._create_lot(expiration_date=expiration_date)
        self.assertEqual(lot.expiration_date, expiration_date)

        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.shopfloor_user_id = self.env.uid

        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = SearchResult(
                record=lot,
                type="lot",
                parse_result=[
                    BarcodeResult(type="unknown", value=lot.name),
                    BarcodeResult(
                        type="expiration_date",
                        value=lot.expiration_date + timedelta(days=2),
                    ),
                ],
            )
            res = self.service.dispatch(
                "scan_lot_name",
                params={
                    "picking_id": picking.id,
                    "selected_line_id": selected_move_line.id,
                    "lot_name": lot.name,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            expiration_date.isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            lot.name,
        )
        self.assertEqual(
            res["message"],
            self.msg_store.lot_already_exists_different_expiration_date(
                lot, lot.expiration_date + timedelta(days=2)
            ),
        )
