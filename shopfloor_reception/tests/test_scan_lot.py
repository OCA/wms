# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date, datetime, timezone
from unittest import mock

from odoo.addons.shopfloor.actions.barcode_parser import BarcodeParser, BarcodeResult

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
        # ↓ Put valid GTIN13 barcodes
        cls.product_a.write({"tracking": "lot", "barcode": "1575138215415"})
        cls.product_b.write({"tracking": "lot", "barcode": "7513645634040"})
        cls.selected_move_line.shopfloor_user_id = cls.env.uid

        return res

    def _get_gs1_parsing_results(
        self, lot, expiration_date_str=None
    ) -> dict[str, BarcodeResult]:
        expiration_date_str = (
            lot.expiration_date.strftime("%y%m%d")
            if lot.expiration_date
            else expiration_date_str or ""
        )
        gs1_barcode = (
            f"{GTIN_AI}{lot.product_id.barcode.zfill(14)}"
            + (
                f"{EXPIRATION_DATE_AI}{expiration_date_str}"
                if expiration_date_str
                else ""
            )
            + f"{LOT_AI}{lot.name}"
        )
        # Note: the order here is important, the first to match a record
        # in DB will determine the `type` (and `record`) of the `SearchResult`
        results = {
            "unknown": BarcodeResult(
                type="unknown", value=gs1_barcode, raw=gs1_barcode
            ),
            # -> Put "product" in first to test if no error in case the
            # SearchResult type is not "lot" but "product" when scaning a lot
            "product": BarcodeResult(
                type="product", value=lot.product_id.barcode, raw=lot.product_id.barcode
            ),
            "lot": BarcodeResult(type="lot", value=lot.name, raw=lot.name),
        }
        if expiration_date_str:
            results["expiration_date"] = BarcodeResult(
                type="expiration_date",
                value=date(
                    int("20" + expiration_date_str[:2]),
                    int(expiration_date_str[2:4]),
                    int(expiration_date_str[4:6]),
                ),
                raw=expiration_date_str,
            )

        return results

    def test_scan_lot_extract_expiration_date_new_lot(self):
        """
        Test that the expiration date can be extracted from barcode scan
        (case when the lot does not already exsit in db)
        """
        lot = self._create_lot(
            product_id=self.product_a.id, expiration_date=datetime(2022, 7, 2)
        )

        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = self._get_gs1_parsing_results(lot)
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": mock_parse.return_value["unknown"].raw,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            datetime.combine(
                lot.expiration_date, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            lot.name,
        )

    def test_scan_lot_extract_expiration_date_existing_lot(self):
        """
        When lot already exists, take the expiration date from the existing lot.

        Ensure there is a warning in case of mismatch between expiration date found in
        the barcode and the one on the existing lot.
        """
        lot = self._create_lot(
            product_id=self.product_a.id, expiration_date=datetime(2022, 7, 2)
        )

        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = self._get_gs1_parsing_results(lot)
            # change expiration date in odoo to make a mismatch with scanned barcode
            lot.expiration_date = datetime(2022, 7, 3)
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": mock_parse.return_value["unknown"].raw,
                },
            )

        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["expiration_date"],
            datetime.combine(
                lot.expiration_date, datetime.min.time(), tzinfo=timezone.utc
            ).isoformat(),
        )
        self.assertEqual(
            res["data"]["set_lot"]["selected_move_line"][0]["lot"]["name"],
            lot.name,
        )
        self.assertMessage(
            res, self.msg_store.lot_already_exists_different_expiration_date(lot)
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
        lot_other_product = self._create_lot(
            product_id=self.product_b.id, expiration_date=datetime(2022, 7, 2)
        )
        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = self._get_gs1_parsing_results(lot_other_product)
            res = self.service.dispatch(
                "scan_lot",
                params={
                    "picking_id": self.picking.id,
                    "selected_line_id": self.selected_move_line.id,
                    "barcode": mock_parse.return_value["unknown"].raw,
                },
            )
        self.assert_response(
            res,
            "set_lot",
            self.msg_store.lot_product_mismatch(),
            data={
                "picking": self.data.picking(self.picking),
                "selected_move_line": self._data_for_move_lines(
                    self.selected_move_line,
                ),
            },
        )

    def test_set_lot_from_select_move(self):
        # Test that time zones are handled correctly
        self.wh.partner_id.sudo().tz = "Europe/Brussels"

        picking = self._create_picking()
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        selected_move_line.product_id.sudo().use_expiration_date = True

        lot = self._create_lot(
            product_id=selected_move_line.product_id.id, expiration_date=None
        )

        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = self._get_gs1_parsing_results(
                lot, expiration_date_str="250415"
            )
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

        # Verify the expiration datetime on the lot is correct in UTC
        # 2025-04-15 00:00:00 Brussels time is 2025-04-14 22:00:00 UTC
        expected_utc = datetime(2025, 4, 14, 22, 0, 0)
        self.assertEqual(selected_move_line.lot_id.expiration_date, expected_utc)
