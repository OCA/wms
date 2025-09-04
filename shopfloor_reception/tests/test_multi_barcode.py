# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl)
import mock

from odoo import fields

from odoo.addons.shopfloor.actions.barcode_parser import BarcodeParser, BarcodeResult

from .common import CommonCase


class TestStructuredBarcode(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product_a.tracking = "lot"
        cls.product_a.use_expiration_date = True
        cls.picking_type.sudo().use_create_lots = True

    def test_scan_multiple_attribute_barcode_fill_lot(self):
        """
        Check that scanning a product with multi attribute barcode
        will fill the lot informations
        """
        picking = self._create_picking()
        lot = self._create_lot()
        lot.expiration_date = fields.Date.to_date("2225-04-15")
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # selected_move_line.lot_id = lot
        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = [
                BarcodeResult(type="lot", value=lot.name, raw=lot.name),
                BarcodeResult(
                    type="expiration_date",
                    value=fields.Date.to_date("2225-04-15"),
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
        data = self.data.picking(picking)
        self.assert_response(
            response,
            next_state="set_lot",
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, expiration_date=True, lot_name=True
                ),
            },
        )
        self.assertEqual(
            selected_move_line.expiration_date,
            fields.Datetime.to_datetime("2225-04-15"),
        )

        self.assertEqual(selected_move_line.lot_id, lot)

    def test_scan_multiple_attribute_barcode_wrong_lot(self):
        """
        Check that scanning a product with multi attribute barcode
        will issue an error if the lot found has a different expiration date
        """
        picking = self._create_picking()
        lot = self._create_lot()
        lot.expiration_date = fields.Date.to_date("2235-04-15")
        selected_move_line = picking.move_line_ids.filtered(
            lambda l: l.product_id == self.product_a
        )
        # selected_move_line.lot_id = lot
        with mock.patch.object(BarcodeParser, "parse") as mock_parse:
            mock_parse.return_value = [
                BarcodeResult(type="lot", value=lot.name, raw=lot.name),
                BarcodeResult(
                    type="expiration_date",
                    value=fields.Date.to_date("2225-04-15"),
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
        data = self.data.picking(picking)
        message_reponse = response.get("message")
        self.assertEqual("error", message_reponse.get("message_type"))

        self.assert_response(
            response,
            next_state="set_lot",
            message=self.service.msg_store.lot_already_exists_different_expiration_date(
                lot, fields.Date.to_date("2225-04-15")
            ),
            data={
                "picking": data,
                "selected_move_line": self.data.move_lines(
                    selected_move_line, expiration_date=True, lot_name=True
                ),
            },
        )

        self.assertFalse(selected_move_line.lot_id)
