# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


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
            locations=self.zone_location,
            package=False,
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
            pickingA.move_ids, in_lot=True, location=self.zone_sublocation2
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

    def test_scan_source_can_not_select_line_with_package(self):
        """Do not allow to scan product with package without scanning pack first."""
        # Picking 1 with one product in a package is already in sub location 1
        pickingA = self._create_picking(lines=[(self.product_a, 13)])
        self._fill_stock_for_moves(
            pickingA.move_ids[0], in_package=True, location=self.zone_sublocation1
        )
        pickingA.action_assign()
        # Scanning a product after having scan a location (sublocation_id)
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.product_a.barcode,
                "sublocation_id": self.zone_sublocation1.id,
            },
        )
        self.assertEqual(response["next_state"], "select_line")
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation1, package=False, product=self.product_a
        )
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            sublocation=self.zone_sublocation1,
            picking_type=self.picking_type,
            message=self.service.msg_store.product_not_found_in_pickings(),
            move_lines=move_lines,
            location_first=True,
        )

    def test_scan_source_scan_location_no_lines_without_package(self):
        """Check list of lines when first scanning location.

        With the scan_location_or_pack_first option on. When scanning first the
        location and no lines without package exist, ask to scan a package.

        """
        # Picking 1 with one product in a package is already in sub location 1
        pickingA = self._create_picking(lines=[(self.product_a, 13)])
        self._fill_stock_for_moves(
            pickingA.move_ids[0], in_package=True, location=self.zone_sublocation1
        )
        pickingA.action_assign()
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.zone_sublocation1.barcode,
            },
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation1, package=False
        )
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            sublocation=self.zone_sublocation1,
            picking_type=self.picking_type,
            message=self.service.msg_store.several_packs_in_location(
                self.zone_sublocation1
            ),
            move_lines=move_lines,
            location_first=True,
        )

    def test_scan_source_scan_package_first_with_two_product(self):
        """Scan a package with two product and then scan a product."""
        pickingA = self._create_picking(lines=[(self.product_a, 13)])
        self._fill_stock_for_moves(
            pickingA.move_ids, in_package=True, location=self.zone_sublocation1
        )
        pickingA.action_assign()
        package = pickingA.package_level_ids[0].package_id

        pickingB = self._create_picking(lines=[(self.product_b, 5)])
        self._fill_stock_for_moves(
            pickingB.move_ids, in_package=package, location=self.zone_sublocation1
        )
        # If all products in package are reserved, it will be handle as a full package
        # pickingB.action_assign()
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": package.name,
            },
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation1, package=package
        )
        self.assertTrue(len(move_lines), 2)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            message=self.service.msg_store.several_products_in_package(package),
            move_lines=move_lines,
            location_first=True,
            package=package,
        )
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_a.barcode, "package_id": package.id},
        )
        move_line = pickingA.move_line_ids[0]
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=13.0,
        )

    def test_scan_source_scan_product_message_product_has_package(self):
        """"""
        # Picking 1 with one product in a package is already in sub location 1
        pickingA = self._create_picking(lines=[(self.product_a, 13)])
        self._fill_stock_for_moves(
            pickingA.move_ids[0], in_package=True, location=self.zone_sublocation1
        )
        pickingA.action_assign()
        # Scanning a product after having scan a location (sublocation_id)
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.product_a.barcode,
                "sublocation_id": self.zone_sublocation1.id,
            },
        )
        self.assertEqual(response["next_state"], "select_line")
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation1, package=False, product=self.product_a
        )
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            sublocation=self.zone_sublocation1,
            picking_type=self.picking_type,
            message=self.service.msg_store.product_not_found_in_pickings(),
            move_lines=move_lines,
            location_first=True,
        )
