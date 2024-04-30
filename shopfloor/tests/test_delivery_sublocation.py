# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_delivery_base import DeliveryCommonCase

# pylint: disable=missing-return


class DeliveryScanSublocationCase(DeliveryCommonCase):
    """Tests sublocation with delivery service."""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.product_e.tracking = "lot"
        # Picking for the top location
        cls.picking = picking = cls._create_picking(
            lines=[
                (cls.product_d, 10),  # D as raw product
                (cls.product_e, 10),  # E as raw product with a lot
            ]
        )
        cls.raw_move = picking.move_ids[0]
        cls.raw_lot_move = picking.move_ids[1]
        cls._fill_stock_for_moves(cls.raw_move)
        cls._fill_stock_for_moves(cls.raw_lot_move, in_lot=True)
        picking.action_assign()
        cls.lot = cls.raw_lot_move.move_line_ids.lot_id
        # Create a sublocation
        cls.sublocation = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Output 1",
                    "location_id": cls.picking_type.default_location_src_id.id,
                    "usage": "internal",
                    "barcode": "WH-OUTPUT-1",
                }
            )
        )
        # Picking for the sublocation
        cls.picking_sublocation = cls._create_picking(
            lines=[
                (cls.product_d, 10),  # D as raw product
                (cls.product_e, 10),  # E as raw product with a lot
            ],
            location_id=cls.sublocation,
        )
        cls.raw_move_sublocation = cls.picking_sublocation.move_ids[0]
        cls.raw_lot_move_sublocation = cls.picking_sublocation.move_ids[1]
        cls._fill_stock_for_moves(cls.raw_move_sublocation, location=cls.sublocation)
        # Use the same lot on product from both picking
        cls._fill_stock_for_moves(
            cls.raw_lot_move_sublocation, in_lot=cls.lot, location=cls.sublocation
        )
        cls.picking_sublocation.action_assign()

    def test_scan_sublocation_exists(self):
        """Check scanning a sublocation sets it as sublocation."""
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.sublocation.barcode,
                "picking_id": None,
                "location_id": None,
            },
        )
        self.assert_response_deliver(
            response,
            picking=None,
            location=self.sublocation,
            message=self.service.msg_store.location_src_set_to_sublocation(
                self.sublocation
            ),
        )

    def test_scan_invalid_barcode_in_sublocation(self):
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": "NO VALID BARCODE",
                "picking_id": None,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_deliver(
            response,
            location=self.sublocation,
            message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_barcode_in_sublocation(self):
        """Scan product barcode that exists in sublocation."""

        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.product_d.barcode,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_deliver(
            response,
            location=self.sublocation,
            picking=self.picking_sublocation,
        )

    def test_scan_product_not_in_sublocation(self):
        """Scan a product in picking type location but not in sublocation set."""
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.product_c.barcode,
                "picking_id": None,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_deliver(
            response,
            location=self.sublocation,
            message=self.service.msg_store.product_not_found_in_pickings(),
        )

    def test_scan_product_exist_in_multiple_sublocation(self):
        """Check scan of product in multiple location will ask to scan a location."""
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.product_d.barcode,
                "picking_id": None,
            },
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.product_in_multiple_sublocation(
                self.product_d
            ),
        )

    def test_list_stock_picking_sublocation(self):
        """Check manual selection filter picking in sublocation."""
        response = self.service.dispatch(
            "list_stock_picking", params={"location_id": self.sublocation.id}
        )
        self.assert_response_manual_selection(
            response,
            pickings=self.picking_sublocation,
        )

    def test_scan_lot_in_sublocation(self):
        """Scan a lot that exists in sublocation."""
        lot = self.raw_lot_move_sublocation.move_line_ids.lot_id
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": lot.name,
                "picking_id": None,
                "location_id": self.sublocation.id,
            },
        )
        self.assert_response_deliver(
            response,
            location=self.sublocation,
            picking=self.picking_sublocation,
        )

    def test_scan_lot_exist_in_multiple_sublocation(self):
        """Check scanning lot in multiple location, will ask location scan first."""
        response = self.service.dispatch(
            "scan_deliver",
            params={
                "barcode": self.lot.name,
                "picking_id": None,
            },
        )
        self.assert_response_deliver(
            response,
            message=self.service.msg_store.lot_in_multiple_sublocation(self.lot),
        )
