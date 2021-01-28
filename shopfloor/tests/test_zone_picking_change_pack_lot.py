# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingChangePackLotCase(ZonePickingCommonCase):
    """Tests for endpoint used from change_pack_lot

    * /change_pack_lot

    Only simple cases are tested to check the flow of responses on success and
    error, the "change.package.lot" component is tested in its own tests.
    """

    def test_change_pack_lot_no_package_or_lot_for_barcode(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_line_ids[0]
        barcode = "UNKNOWN"
        response = self.service.dispatch(
            "change_pack_lot",
            params={"move_line_id": move_line.id, "barcode": barcode},
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
            params={"move_line_id": move_line.id, "barcode": self.free_package.name},
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
            params={"move_line_id": move_line.id, "barcode": self.free_lot.name},
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
