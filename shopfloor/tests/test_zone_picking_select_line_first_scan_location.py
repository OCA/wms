# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSelectLineFirstScanLocationCase(ZonePickingCommonCase):
    """Tests for endpoint used from select_line with option 'First scan location'

    * /scan_source

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id
        self.menu.sudo().scan_location_or_pack_first = True

    def test_scan_source_first_the_product_not_ok(self):
        """Check first scanning a product barcode is not allowed."""
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_a.barcode},
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_location
        )
        self.assertTrue(response.get("data").get("select_line"))
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            message=self.service.msg_store.barcode_not_found(),
            move_lines=move_lines,
            location_first=True,
        )

    def test_scan_source_scan_location_then_product_ok(self):
        """Check scanning location and then product is fine."""
        # Have the same product multiple time in sublocation 2
        pickingA = self._create_picking(
            lines=[(self.product_b, 12), (self.product_c, 13)]
        )
        self._fill_stock_for_moves(
            pickingA.move_lines, in_lot=True, location=self.zone_sublocation2
        )
        pickingA.action_assign()
        # Scan product B, send sublocation to simulate a previous scan for a location
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.product_b.barcode,
                "sublocation_id": self.zone_sublocation2.id,
            },
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation2, product=self.product_b
        )
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            message=self.service.msg_store.several_move_with_different_lot(),
            move_lines=move_lines,
            product=self.product_b,
            sublocation=self.zone_sublocation2,
            location_first=True,
        )
