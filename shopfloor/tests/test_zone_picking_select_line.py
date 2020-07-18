from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSelectLineCase(ZonePickingCommonCase):
    """Tests for endpoint used from select_line

    * /list_move_lines (to change order)
    * /scan_source

    """

    def test_list_move_lines_order_by_location(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        # Ensure that the second location is ordered before the first one
        # to avoid "false-positive" checks
        self.zone_sublocation2.name = "a " + self.zone_sublocation2.name
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "order": "location",
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        move_lines = move_lines.sorted(lambda l: l.location_id.name)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )

    def test_scan_source_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "barcode": self.zone_sublocation1.barcode,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "barcode": self.zone_sublocation1.barcode,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_scan_source_barcode_location_not_allowed(self):
        """Scan source: scanned location not allowed."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.customer_location.barcode,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_source_barcode_location_one_move_line(self):
        """Scan source: scanned location 'Zone sub-location 1' contains only
        one move line, next step 'set_line_destination' expected.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.zone_sublocation1.barcode,
            },
        )
        move_line = self.picking1.move_line_ids
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
        )

    def test_scan_source_barcode_location_several_move_lines(self):
        """Scan source: scanned location 'Zone sub-location 2' contains two
        move lines, next step 'select_line' expected with the list of these
        move lines.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.zone_sublocation2.barcode,
            },
        )
        move_lines = self.picking2.move_line_ids
        self.assert_response_select_line(
            response,
            zone_location=self.zone_sublocation2,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.several_lines_in_location(
                self.zone_sublocation2
            ),
        )

    def test_scan_source_barcode_package(self):
        """Scan source: scanned package has one related move line,
        next step 'set_line_destination' expected on it.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        package = self.picking1.package_level_ids[0].package_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": package.name,
            },
        )
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, package=package,
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        move_line = move_lines[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
        )

    def test_scan_source_barcode_package_not_found(self):
        """Scan source: scanned package has no related move line,
        next step 'select_line' expected.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.free_package.name,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.package_not_found(),
        )

    def test_scan_source_barcode_product(self):
        """Scan source: scanned product has one related move line,
        next step 'set_line_destination' expected on it.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.product_a.barcode,
            },
        )
        move_line = self.service._find_location_move_lines(
            zone_location, picking_type, product=self.product_a,
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
        )

    def test_scan_source_barcode_product_not_found(self):
        """Scan source: scanned product has no related move line,
        next step 'select_line' expected.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.free_product.barcode,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.product_not_found(),
        )

    def test_scan_source_barcode_lot(self):
        """Scan source: scanned lot has one related move line,
        next step 'set_line_destination' expected on it.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        lot = self.picking2.move_line_ids.lot_id[0]
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": lot.name,
            },
        )
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, lot=lot,
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        move_line = move_lines[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
        )

    def test_scan_source_barcode_lot_not_found(self):
        """Scan source: scanned lot has no related move line,
        next step 'select_line' expected.
        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.free_lot.name,
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.lot_not_found(),
        )

    def test_scan_source_barcode_not_found(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": "UNKNOWN",
            },
        )
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.barcode_not_found(),
        )
