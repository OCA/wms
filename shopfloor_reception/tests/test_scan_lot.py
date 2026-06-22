# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timezone
from unittest import mock

from odoo.addons.shopfloor.actions.barcode_parser import BarcodeParser, BarcodeResult
from odoo.addons.shopfloor.actions.search import SearchAction, SearchResult

from .common import CommonCase

UTC = timezone.utc
GTIN_AI = "01"
LOT_AI = "10"
EXPIRATION_DATE_AI = "17"


class TestScanLotName(CommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        res = super().setUpClassBaseData()

        cls.picking = cls._create_picking()
        cls.lot = cls._create_lot()
        cls.selected_move_line = cls.picking.move_line_ids.filtered(
            lambda l: l.product_id == cls.product_a
        )
        # ↓ Put a barcode compatible with GS1
        cls.product_a.write({"tracking": "lot", "barcode": "11111111111111"})
        cls.selected_move_line.shopfloor_user_id = cls.env.uid

        return res

    def _generate_gs1(
        self, product_barcode: str, lot_expiration_date: date, lot_name: str
    ) -> str:
        gs1_barcode = (
            f"{GTIN_AI}{product_barcode}"
            f"{EXPIRATION_DATE_AI}{lot_expiration_date.strftime('%y%m%d')}"
            f"{LOT_AI}{lot_name}"
        )
        return gs1_barcode

    def _generate_search_result(
        self,
        full_barcode: str,
        expiration_date: date,
        lot_name: str,
        product_barcode: str,
        _type="none",
        record=None,
    ) -> SearchResult:
        return SearchResult(
            record=record,
            type=_type,
            parse_result=[
                BarcodeResult(type="unknown", value=full_barcode, raw=full_barcode),
                BarcodeResult(
                    type="expiration_date",
                    value=expiration_date,
                    raw=expiration_date.strftime("%y%m%d"),
                ),
                BarcodeResult(type="lot", value=lot_name, raw=lot_name),
                BarcodeResult(
                    type="product", value=product_barcode, raw=product_barcode
                ),
            ],
        )

    def test_scan_lot_extract_expiration_date_new_lot(self):
        """
        Test that the expiration date can be extracted from barcode scan
        (case when the lot does not already exsit in db)
        """
        expiration_date = date(2022, 7, 2)
        gs1_barcode = self._generate_gs1(
            self.product_a.barcode, expiration_date, self.lot.name
        )

        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = self._generate_search_result(
                gs1_barcode, expiration_date, self.lot.name, self.product_a.barcode
            )
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": self.lot.name,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            datetime(
                expiration_date.year, expiration_date.month, expiration_date.day
            ).isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            self.lot.name,
        )

    def test_scan_lot_extract_expiration_date_existing_lot(self):
        """
        When lot already exists, take the expiration date from the existing lot.

        Ensure there is a warning in case of mismatch between expiration date found in
        the barcode and the one on the existing lot.
        """
        expiration_date = date(2022, 7, 2)
        gs1_barcode = self._generate_gs1(
            self.product_a.barcode, expiration_date, self.lot.name
        )

        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = self._generate_search_result(
                gs1_barcode,
                expiration_date,
                self.lot.name,
                self.product_a.barcode,
                _type="lot",
                record=self.lot,
            )
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": self.lot.name,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            datetime(
                expiration_date.year, expiration_date.month, expiration_date.day
            ).isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            self.lot.name,
        )
        self.assertMessage(
            res, self.msg_store.lot_already_exists_different_expiration_date(self.lot)
        )

    def test_scan_lot_name_auto_set_lot_on_move_line(self):
        """
        If lot exists and lot_name is set on the move line,
        auto-fill the lot_id and skip "sel_lot" state.
        """
        self.selected_move_line.lot_name = self.lot.name

        res = self.service.dispatch(
            "scan_line",
            params={
                "picking_id": self.picking.id,
                "barcode": self.lot.name,
            },
        )

        self.assertEqual(res["next_state"], "set_quantity")
        self.assertEqual(self.selected_move_line.lot_id, self.lot)

    def test_scan_lot_wrong_product(self):
        """
        Test that the system detects that the scanned lot is for another product
        than currently selected one.
        """
        expiration_date = date(2022, 7, 2)
        other_product_barcode = "01223334444555"
        gs1_barcode = self._generate_gs1(
            other_product_barcode, expiration_date, self.lot.name
        )

        with mock.patch.object(SearchAction, "find") as mock_find:
            mock_find.return_value = self._generate_search_result(
                gs1_barcode, expiration_date, self.lot.name, other_product_barcode
            )
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": self.lot.name,
                },
            )
        self.assert_response(
            res,
            "set_lot",
            self.msg_store.lot_product_mismatch(),
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self._data_for_move_lines(
                    self.selected_move_line
                ),
            },
        )

    def test_set_lot_from_select_move(self):
        picking = self._create_picking()
        lot = self._create_lot()
        lot.expiration_date = None
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # selected_move_line.lot_id = lot
        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            # Note: the order here is important, the first to match a record
            # in DB will determine the `type` (and `record`) of the `SearchResult`
            mock_parse.return_value = [
                # -> Put "product" in first to test if no error in case the
                # SearchResult type is not "lot" but "product"
                BarcodeResult(
                    type="product",
                    value=selected_move_line.product_id.barcode,
                    raw=selected_move_line.product_id.barcode,
                ),
                BarcodeResult(type="lot", value=lot.name, raw=lot.name),
                BarcodeResult(
                    type="expiration_date",
                    value=date(2025, 4, 15),
                    raw="250415",
                ),
            ]
            response = self.service.dispatch(
                "scan_line",
                params={
                    "picking_id": picking.id,
                    "barcode": lot.name,
                },
            )
        self.assert_response(
            response,
            next_state="set_quantity",
            data={
                "picking": self.data.picking(picking),
                "selected_move_line": self._data_for_move_lines(selected_move_line),
                "confirmation_required": None,
            },
        )
