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


class TestLocationContentTransferScanLocationSameProduct(
    LocationContentTransferCommonCase
):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        # If the product is available in several sub locations of the picking
        # location (a view) and the scanned location is one of those children,
        cls.parent = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Transfer",
                    "location_id": cls.wh.view_location_id.id,
                }
            )
        )
        cls.child_1 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Child 1",
                    "location_id": cls.parent.id,
                    "barcode": "L#CHILD01",
                }
            )
        )
        cls.child_2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Child 2",
                    "location_id": cls.parent.id,
                    "barcode": "L#CHILD02",
                }
            )
        )
        cls.p_type = (
            cls.env["stock.picking.type"]
            .sudo()
            .create(
                {
                    "name": "Transfer Test",
                    "sequence_code": "TRANS-TEST",
                    "default_location_dest_id": cls.wh.lot_stock_id.id,
                    "default_location_src_id": cls.parent.id,
                }
            )
        )
        cls.menu.sudo().picking_type_ids = cls.p_type

        cls._update_qty_in_location(cls.child_1, cls.product_a, 10.0)
        cls._update_qty_in_location(cls.child_2, cls.product_a, 10.0)
        cls.picking1 = cls._create_picking(
            lines=[(cls.product_a, 12)], picking_type=cls.p_type
        )
        cls.picking1.move_type = "one"
        cls.picking1.action_assign()

        # During the mean time, the location has been filled in
        cls._update_qty_in_location(cls.child_2, cls.product_a, 300.0)

        cls.picking1.move_line_ids[1].reserved_uom_qty = 300.0

    def test_lines_returned_by_scan_location(self):
        """Check that lines from not ready pickings are not offered to work on."""
        self.picking1.move_line_ids[1].location_dest_id = self.shelf1

        response = self.service.dispatch(
            "scan_location", params={"barcode": self.child_2.barcode}
        )
        lines = response["data"]["scan_destination_all"]["move_lines"]
        line_ids = [line["id"] for line in lines]
        self.assertTrue(self.picking1.move_line_ids[0].id not in line_ids)
