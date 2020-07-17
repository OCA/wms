from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingStartCase(ZonePickingCommonCase):
    """Tests for endpoint used from start

    * /scan_location

    """

    def test_scan_location_wrong_barcode(self):
        """Scanned location invalid, no location found."""
        response = self.service.dispatch(
            "scan_location", params={"barcode": "UNKNOWN LOCATION"},
        )
        self.assert_response_start(
            response, message=self.service.msg_store.no_location_found(),
        )

    def test_scan_location_not_allowed(self):
        """Scanned location not allowed because it's not a child of picking
        types' source location.
        """
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.customer_location.barcode},
        )
        self.assert_response_start(
            response, message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_location_no_move_lines(self):
        """Scanned location valid, but no move lines found in it."""
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.shelf2.barcode},
        )
        self.assert_response_start(
            response, message=self.service.msg_store.no_lines_to_process(),
        )

    def test_scan_location_ok(self):
        """Scanned location valid, list of picking types of related move lines."""
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.zone_location.barcode},
        )
        self.assert_response_select_picking_type(
            response, zone_location=self.zone_location, picking_types=self.picking_type,
        )
