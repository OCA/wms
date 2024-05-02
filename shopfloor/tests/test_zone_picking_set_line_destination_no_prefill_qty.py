# Copyright 2022 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase


# pylint: disable=missing-return
class ZonePickingSetLineDestinationNoPrefillQtyCase(ZonePickingCommonCase):
    """Tests for endpoint used from set_line_destination

    With the no prefill quantity option set

    * /set_destination
    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking2.picking_type_id
        self.menu.sudo().no_prefill_qty = True

    def test_set_destination_increment_with_product(self):
        """Check increment quantity by scanning the product."""
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids[0]
        # Scan twice the product in a row to increment the quantity
        for qty_done in range(2):
            response = self.service.dispatch(
                "set_destination",
                params={
                    "move_line_id": move_line.id,
                    "barcode": move_line.product_id.barcode,
                    "quantity": qty_done,
                },
            )
            qty_done += 1
            # Check response
            self.assert_response_set_line_destination(
                response,
                self.zone_location,
                picking_type,
                move_line,
                qty_done=qty_done,
            )

    def test_set_destination_increment_with_wrong_package(self):
        """Check scanning wrong package incremented quantity is not lost."""
        wrong_package = self.picking1.move_line_ids.package_id
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids[0]
        # Simulate the product has been scanned twice
        qty_done = 2
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": wrong_package.name,
                "quantity": qty_done,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            self.zone_location,
            picking_type,
            move_line,
            qty_done=qty_done,
            message={
                "body": "Package {} is not empty.".format(wrong_package.name),
                "message_type": "warning",
            },
        )

    def test_set_destination_increment_with_wrong_product(self):
        """Check increment quantity by scanning the wrong product."""
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids[0]
        # Scan twice the product in a row to increment the quantity
        qty_done = 2
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.product_a.barcode,
                "quantity": qty_done,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            self.zone_location,
            picking_type,
            move_line,
            qty_done=qty_done,
            message={"body": "The package A doesn't exist", "message_type": "error"},
        )

    def test_set_destination_increment_with_lot(self):
        """Check increment quantity by scanning the lot."""
        picking_type = self.picking2.picking_type_id
        move_line = self.picking2.move_line_ids.filtered("lot_id")[0]
        # Scan twice the lot in a row to increment the quantity
        for qty_done in range(2):
            response = self.service.dispatch(
                "set_destination",
                params={
                    "move_line_id": move_line.id,
                    "barcode": move_line.lot_id.name,
                    "quantity": qty_done,
                },
            )
            qty_done += 1
            # Check response
            self.assert_response_set_line_destination(
                response,
                self.zone_location,
                picking_type,
                move_line,
                qty_done=qty_done,
            )

    def test_set_destination_location_zero_quantity(self):
        """Scanned barcode is the destination location.

        Quantity to move is zero -> error raised, user can try again.

        """
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking1.move_ids.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.packing_location.barcode,
                "quantity": 0,
            },
        )
        # Check response
        self.assert_response_set_line_destination(
            response,
            zone_location,
            picking_type,
            move_line,
            message=self.service.msg_store.picking_zero_quantity(),
            # And that the quantity done is zero
            qty_done=0,
        )
