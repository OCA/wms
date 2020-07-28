from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingChangePackLotCase(ZonePickingCommonCase):
    """Tests for endpoint used from change_pack_lot

    * /change_pack_lot

    """

    def test_change_pack_lot_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": self.free_lot.name,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
                "move_line_id": move_line.id,
                "barcode": self.free_lot.name,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": 1234567890,
                "barcode": self.free_lot.name,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_change_pack_lot_no_package_or_lot_for_barcode(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        barcode = "UNKNOWN"
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": barcode,
            },
        )
        self.assert_response_change_pack_lot(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.no_package_or_lot_for_barcode(barcode),
        )

    def test_change_pack_lot_change_pack_ok(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        previous_package = move_line.package_id
        # ensure we have our new package in the same location
        self._update_qty_in_location(
            move_line.location_id,
            move_line.product_id,
            move_line.product_uom_qty,
            package=self.free_package,
        )
        # change package
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
            },
        )
        # check data
        self.assertRecordValues(
            move_line,
            [
                {
                    "package_id": self.free_package.id,
                    "result_package_id": self.free_package.id,
                }
            ],
        )
        self.assertRecordValues(
            move_line.package_level_id, [{"package_id": self.free_package.id}]
        )
        # check that reservations have been updated
        previous_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("package_id", "=", previous_package.id),
            ]
        )
        self.assertEqual(previous_quant.quantity, 10)
        self.assertEqual(previous_quant.reserved_quantity, 0)
        new_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("package_id", "=", self.free_package.id),
            ]
        )
        self.assertEqual(new_quant.quantity, 10)
        self.assertEqual(new_quant.reserved_quantity, 10)
        # check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.package_replaced_by_package(
                previous_package, self.free_package
            ),
        )

    def test_change_pack_lot_change_lot_ok(self):
        zone_location = self.zone_location
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids[0]
        previous_lot = move_line.lot_id
        self.free_lot.product_id = move_line.product_id
        # ensure we have our new lot in the same location
        self._update_qty_in_location(
            move_line.location_id,
            move_line.product_id,
            move_line.product_uom_qty,
            lot=self.free_lot,
        )
        # change lot
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": self.free_lot.name,
            },
        )
        # check data
        self.assertRecordValues(move_line, [{"lot_id": self.free_lot.id}])
        # check that reservations have been updated
        previous_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("lot_id", "=", previous_lot.id),
            ]
        )
        self.assertEqual(previous_quant.quantity, 10)
        self.assertEqual(previous_quant.reserved_quantity, 0)
        new_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("lot_id", "=", self.free_lot.id),
            ]
        )
        self.assertEqual(new_quant.quantity, 10)
        self.assertEqual(new_quant.reserved_quantity, 10)
        # check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.lot_replaced_by_lot(
                previous_lot, self.free_lot
            ),
        )

    def test_change_pack_lot_change_lot_ok_with_control_stock(self):
        zone_location = self.zone_location
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids[0]
        previous_lot = move_line.lot_id
        self.free_lot.product_id = move_line.product_id
        # ensure we have our new lot but in another location
        self._update_qty_in_location(
            self.zone_sublocation1,
            move_line.product_id,
            move_line.product_uom_qty,
            lot=self.free_lot,
        )
        # change lot
        response = self.service.dispatch(
            "change_pack_lot",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": self.free_lot.name,
            },
        )
        # check data
        self.assertRecordValues(move_line, [{"lot_id": self.free_lot.id}])
        # check that reservations could not be made as the lot is
        # theoretically elsewhere
        previous_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("lot_id", "=", previous_lot.id),
            ]
        )
        self.assertEqual(previous_quant.quantity, 10)
        self.assertEqual(previous_quant.reserved_quantity, 0)
        new_quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", move_line.location_id.id),
                ("product_id", "=", move_line.product_id.id),
                ("lot_id", "=", self.free_lot.id),
            ]
        )
        self.assertFalse(new_quant)
        # as such an inventory of control has been generated to check this issue
        control_inventory_name = "Pick: stock issue on lot: {} found in {}".format(
            self.free_lot.name, move_line.location_id.name
        )
        control_inventory = self.env["stock.inventory"].search(
            [
                ("name", "=", control_inventory_name),
                ("location_ids", "in", move_line.location_id.id),
                ("product_ids", "in", move_line.product_id.id),
                ("state", "in", ("draft", "confirm")),
            ]
        )
        self.assertTrue(control_inventory)
        # check response
        message = self.service.msg_store.lot_replaced_by_lot(
            previous_lot, self.free_lot
        )
        message["body"] += " A draft inventory has been created for control."
        self.assert_response_set_line_destination(
            response, zone_location, picking_type, move_line, message=message,
        )
