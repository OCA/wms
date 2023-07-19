# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

from .test_location_content_transfer_base import LocationContentTransferCommonCase

# pylint: disable=missing-return


class TestLocationContentTransferScanLocation(LocationContentTransferCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # One picking with shipping policy set on "When all products are ready"
        # With only one of the move available in the stock
        cls.picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking1.move_type = "one"
        cls.move1 = cls.picking1.move_ids[0]
        cls._fill_stock_for_moves(cls.move1, in_package=False, location=cls.content_loc)
        cls.picking1.action_assign()
        # Another picking available
        picking2 = cls._create_picking(lines=[(cls.product_c, 5)])
        cls._fill_stock_for_moves(picking2.move_ids, location=cls.content_loc)
        picking2.action_assign()

    def test_lines_returned_by_scan_location(self):
        """Check that lines from not ready pickings are not offered to work on."""
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        lines = response["data"]["scan_destination_all"]["move_lines"]
        line_ids = [line["id"] for line in lines]
        self.assertTrue(self.move1.move_line_ids.id not in line_ids)
