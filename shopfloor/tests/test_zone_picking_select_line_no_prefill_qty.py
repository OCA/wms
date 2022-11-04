# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSelectLineCase(ZonePickingCommonCase):
    """Tests for endpoint used from select_line with no prefill quantity

    * /scan_source

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id
        self.menu.sudo().no_prefill_qty = True

    def test_scan_source_barcode_location_no_prefill(self):
        """When a location is scanned, qty_done in response is False."""
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.zone_sublocation1.barcode},
        )
        move_line = self.picking1.move_line_ids
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=False,
        )

    def test_scan_source_barcode_package_no_prefill(self):
        """When a package is scanned, qty_done in response is False."""
        package = self.picking1.package_level_ids[0].package_id
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": package.name},
        )
        move_lines = self.service._find_location_move_lines(
            package=package,
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        move_line = move_lines[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=False,
        )

    def test_scan_source_barcode_product_no_prefill(self):
        """When a product is scanned, qty_done in response is 1.0."""
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_a.barcode},
        )
        move_line = self.service._find_location_move_lines(
            product=self.product_a,
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=1.0,
        )

    def test_scan_source_barcode_lot_no_prefill(self):
        """When a lot is scanned, qty_done in response is 1.0"""
        lot = self.picking2.move_line_ids.lot_id[0]
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": lot.name},
        )
        move_lines = self.service._find_location_move_lines(lot=lot)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        move_line = move_lines[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=1.0,
        )

    def test_scan_source_barcode_packaging_no_prefill(self):
        """Check qty_done for packaginge scan with no_prefill."""
        packaging = self.product_a_packaging
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": packaging.barcode},
        )
        move_line = self.service._find_location_move_lines(
            product=self.product_a,
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=packaging.qty,
        )
