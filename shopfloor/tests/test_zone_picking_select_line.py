# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo import fields

from .test_zone_picking_base import ZonePickingCommonCase


class ZonePickingSelectLineCase(ZonePickingCommonCase):
    """Tests for endpoint used from select_line

    * /list_move_lines (to change order)
    * /scan_source
    * /prepare_unload

    """

    def setUp(self):
        super().setUp()
        self.service.work.current_picking_type = self.picking1.picking_type_id

    def test_list_move_lines_order(self):
        self.zone_sublocation2.name = "AAA " + self.zone_sublocation2.name

        # Test by location
        today = fields.Datetime.today()
        future = fields.Datetime.add(
            fields.Datetime.end_of(fields.Datetime.today(), "day"), days=2
        )
        # change date to lines in the same location
        move1 = self.picking2.move_lines[0]
        move1.write({"date": today})
        move1_line = move1.move_line_ids[0]
        move2 = self.picking2.move_lines[1]
        move2.write({"date": future})
        move2_line = move2.move_line_ids[0]

        self.service.work.current_lines_order = "location"
        move_lines = self.service._find_location_move_lines()
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertTrue(order_mapping[move1_line] < order_mapping[move2_line])

        # swap dates
        move2.write({"date": today})
        move1.write({"date": future})
        move_lines = self.service._find_location_move_lines()
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertTrue(order_mapping[move1_line] > order_mapping[move2_line])

        # Test by priority
        self.picking2.write({"priority": "0"})
        (self.pickings - self.picking2).write({"priority": "1"})

        self.service.work.current_lines_order = "priority"
        move_lines = self.service._find_location_move_lines()
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        # picking2 lines stay at the end as they are low priority
        self.assertTrue(move1_line in move_lines[-2:])
        self.assertTrue(move2_line in move_lines[-2:])
        # but move1_line comes after the other
        self.assertTrue(order_mapping[move1_line] > order_mapping[move2_line])

        # swap dates again
        move2.write({"date": future})
        move1.write({"date": today})
        # and increase priority
        self.picking2.write({"priority": "1"})
        (self.pickings - self.picking2).write({"priority": "0"})
        move_lines = self.service._find_location_move_lines()
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertEqual(order_mapping[move1_line], 0)
        self.assertEqual(order_mapping[move2_line], 1)

    def test_list_move_lines_order_by_location(self):
        self.service.work.current_lines_order = "location"
        response = self.service.dispatch("list_move_lines", params={})
        move_lines = self.service._find_location_move_lines()
        res = [
            x["location_src"]["name"]
            for x in response["data"]["select_line"]["move_lines"]
        ]
        self.assertEqual(res, [x.location_id.name for x in move_lines])
        self.maxDiff = None
        self.assert_response_select_line(
            response,
            self.zone_location,
            self.picking1.picking_type_id,
            move_lines,
        )

    def test_list_move_lines_order_by_priority(self):
        response = self.service.dispatch("list_move_lines", params={})
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            self.zone_location,
            self.picking_type,
            move_lines,
        )

    def test_scan_source_barcode_location_not_allowed(self):
        """Scan source: scanned location not allowed."""
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.customer_location.barcode},
        )
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            self.zone_location,
            self.picking_type,
            move_lines,
            message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_source_barcode_location_one_move_line(self):
        """Scan source: scanned location 'Zone sub-location 1' contains only
        one move line, next step 'set_line_destination' expected.
        """
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
            qty_done=10.0,
        )

    def test_scan_source_barcode_location_two_move_lines_same_product(self):
        """Scan source: scanned location 'Zone sub-location 1' contains two lines.

        Lines have the same product/package/lot,
        they get processed one after the other,
        next step 'set_line_destination' expected.
        """
        package = self.picking1.move_line_ids.mapped("package_id")[0]
        new_picking = self._create_picking(lines=[(self.product_a, 20)])
        self._fill_stock_for_moves(
            new_picking.move_lines, in_package=package, location=self.zone_sublocation1
        )
        new_picking.action_assign()
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
            qty_done=10.0,
        )
        # first line done
        move_line.qty_done = move_line.product_uom_qty
        # get the next one
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.zone_sublocation1.barcode},
        )
        move_line = new_picking.move_line_ids
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=10.0,
        )

    def test_scan_source_barcode_location_several_move_lines(self):
        """Scan source: scanned location 'Zone sub-location 2' contains two
        move lines, next step 'select_line' expected with the list of these
        move lines.
        """
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.zone_sublocation2.barcode},
        )
        move_lines = self.picking2.move_line_ids
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.several_products_in_location(
                self.zone_sublocation2
            ),
            sublocation=self.zone_sublocation2,
            location_first=False,
        )

    def test_scan_source_barcode_package(self):
        """Scan source: scanned package has one related move line,
        next step 'set_line_destination' expected on it.
        """
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
            qty_done=10.0,
        )

    def test_scan_source_barcode_package_not_found(self):
        """Scan source: scanned package has no related move line,
        next step 'select_line' expected.
        """
        self.free_package.location_id = self.zone_location
        pack_code = self.free_package.name
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": pack_code},
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.package_has_no_product_to_take(pack_code),
        )

    def test_scan_source_barcode_package_not_exist(self):
        """Scan source: scanned package that does not exist in the system
        next step 'select_line' expected.
        """
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": "P-Unknown"},
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_source_package_many_products(self):
        """Scan source: scanned package that several product, aborting
        next step 'select_line expected.

        This is only when no prefill quantity option is enabled. If not
        the related package will be move in one step.
        """
        self.menu.sudo().no_prefill_qty = True
        pack = self.picking1.package_level_ids[0].package_id
        self._update_qty_in_location(pack.location_id, self.product_b, 2, pack)
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": pack.name},
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation1
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            package=pack,
            message=self.service.msg_store.several_products_in_package(pack),
            location_first=False,
        )

    def test_scan_source_empty_package(self):
        """Scan source: scanned an empty package."""
        pack_empty = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": pack_empty.name},
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_location
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.package_has_no_product_to_take(
                pack_empty.name
            ),
            location_first=False,
        )

    def test_scan_source_barcode_package_can_replace_in_line(self):
        """Scan source: scanned package has no related line but can replace
        next step 'select_line' expected with confirmation required set.
        Scan source: 2nd time the package replace package line with new package
        next step 'set_line_destination'.
        """
        # Add the same product same package in the same location to use as replacement
        picking1b = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(
            picking1b.move_lines, in_package=True, location=self.zone_sublocation1
        )
        picking1b.action_assign()
        picking1b.action_cancel()
        package1b = picking1b.package_level_ids[0].package_id
        package1 = self.picking1.package_level_ids[0].package_id
        # 1st scan
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": package1b.name},
        )
        move_lines = self.service._find_location_move_lines(
            package=package1,
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.package_different_change(),
            confirmation_required=True,
        )
        self.assertEqual(self.picking1.package_level_ids[0].package_id, package1)
        # 2nd scan
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": package1b.name, "confirmation": True},
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_lines[0],
            message=self.service.msg_store.package_replaced_by_package(
                package1, package1b
            ),
            qty_done=self.service._get_prefill_qty(move_lines[0]),
        )
        # Check the package has been changed on the move line
        self.assertEqual(self.picking1.package_level_ids[0].package_id, package1b)

    def test_scan_source_barcode_product(self):
        """Scan source: scanned product has one related move line,
        next step 'set_line_destination' expected on it.
        """
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
            qty_done=10.0,
        )

    def test_scan_source_barcode_product_not_found(self):
        """Scan source: scanned product has no related move line,
        next step 'select_line' expected.
        """
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.free_product.barcode},
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.product_not_found_in_pickings(),
        )

    def test_scan_source_barcode_product_multiple_moves_different_location(self):
        """Scan source: scanned product has move lines in multiple sub location.

        next step : 'select_line' expected.

        Then scan a location and a specific line is selected.

        next step : 'set_line_destination'
        """
        # Using picking4 which has a product in two sublocation
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_e.barcode},
        )
        move_lines = self.service._find_location_move_lines(product=self.product_e)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            product=self.product_e,
            message=self.service.msg_store.several_move_in_different_location(),
        )
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.zone_sublocation3.barcode,
                "product_id": self.product_e.id,
            },
        )
        self.assertEqual(response["next_state"], "set_line_destination")
        move_line = self.service._find_location_move_lines(
            product=self.product_e, locations=self.zone_sublocation3
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=6.0,
        )

    def test_scan_source_barcode_location_multiple_moves_different_product(self):
        """Scan source: scanned location has move lines with multiple product.

        next step : 'select_line' expected.

        Then scan a product and a specific line is selected.

        next step : 'set_line_destination'
        """
        # Using picking4 which has a product in two sublocation
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.zone_sublocation3.barcode},
        )
        move_lines = self.service._find_location_move_lines(
            locations=self.zone_sublocation3
        )
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            sublocation=self.zone_sublocation3,
            message=self.service.msg_store.several_products_in_location(
                self.zone_sublocation3
            ),
            location_first=False,
        )
        response = self.service.dispatch(
            "scan_source",
            params={
                "barcode": self.product_e.barcode,
                "sublocation_id": self.zone_sublocation3.id,
            },
        )
        self.assertEqual(response["next_state"], "set_line_destination")
        move_line = self.service._find_location_move_lines(
            product=self.product_e, locations=self.zone_sublocation3
        )
        self.assert_response_set_line_destination(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_line=move_line,
            qty_done=6.0,
        )

    def test_scan_source_barcode_product_with_multiple_lot(self):
        """Scan source: scanned product is found with mulitple lot number.

        next step : 'select_line' expected.
        """
        # Product C has already one lot from test_zone_picking_base.py
        # So lets add one more lot for that product in same location.
        pick = self._create_picking(lines=[(self.product_c, 10)])
        self._fill_stock_for_moves(
            pick.move_lines, in_lot=True, location=self.zone_sublocation2
        )
        pick.action_assign()
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.product_c.barcode},
        )
        move_lines = self.service._find_location_move_lines(product=self.product_c)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            product=self.product_c,
            message=self.service.msg_store.several_move_with_different_lot(),
        )

    def test_scan_source_barcode_lot(self):
        """Scan source: scanned lot has one related move line,
        next step 'set_line_destination' expected on it.
        """
        # Product C has already one lot from test_zone_picking_base.py
        # So lets add one more lot for that product in a different location.
        pick = self._create_picking(lines=[(self.product_c, 10)])
        self._fill_stock_for_moves(
            pick.move_lines, in_lot=True, location=self.zone_sublocation1
        )
        pick.action_assign()
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
            qty_done=10.0,
        )

    def test_scan_source_barcode_lot_in_multiple_location(self):
        """Scan source: scanned lot is in multiple location
        next step 'select_line' expected on it.
        """
        # Picking 2 has already some lot from test_zone_picking_base.py
        # So lets add in the same lot the same product in another location.
        lot = self.picking2.move_line_ids.lot_id[0]
        picking = self._create_picking(lines=[(lot.product_id, 2)])
        self._fill_stock_for_moves(
            picking.move_lines, in_lot=lot, location=self.zone_sublocation3
        )
        picking.action_assign()
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": lot.name},
        )
        # FIX ME: need to filter lines only on lot scanned !!
        move_lines = self.service._find_location_move_lines()
        # move_lines = self.service._find_location_move_lines(lot=lot)
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.several_move_in_different_location(),
        )

    def test_scan_source_barcode_lot_not_found(self):
        """Scan source: scanned lot has no related move line,
        next step 'select_line' expected.
        """
        response = self.service.dispatch(
            "scan_source",
            params={"barcode": self.free_lot.name},
        )
        move_lines = self.service._find_location_move_lines()
        move_lines = move_lines.sorted(lambda l: l.move_id.priority, reverse=True)
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.lot_not_found_in_pickings(),
        )

    def test_scan_source_barcode_not_found(self):
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": self.zone_location.id,
                "picking_type_id": self.picking_type.id,
                "barcode": "UNKNOWN",
            },
        )
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            zone_location=self.zone_location,
            picking_type=self.picking_type,
            move_lines=move_lines,
            message=self.service.msg_store.barcode_not_found(),
        )

    def test_scan_source_multi_users(self):
        """First user scans the source location 'Zone sub-location 1' containing
        only one move line, then processes the next step 'set_line_destination'.

        The second user scans the same source location, and should not find any line.
        """
        # The first user starts to process the only line available
        #   - scan source
        response = self.service.scan_source(
            self.zone_sublocation1.barcode,
        )
        move_line = self.picking1.move_line_ids
        self.assertEqual(response["next_state"], "set_line_destination")
        #   - set destination
        self.service.set_destination(
            move_line.id,
            self.free_package.name,
            move_line.product_uom_qty,
        )
        self.assertEqual(move_line.shopfloor_user_id, self.env.user)
        # The second user scans the same source location
        env = self.env(user=self.stock_user2)
        with self.work_on_services(
            env=env,
            menu=self.menu,
            profile=self.profile,
            current_zone_location=self.zone_location,
            current_picking_type=self.picking_type,
        ) as work:
            service = work.component(usage="zone_picking")
            response = service.scan_source(
                self.zone_sublocation1.barcode,
            )
            self.assertEqual(response["next_state"], "select_line")
            self.assertEqual(
                response["message"],
                self.service.msg_store.wrong_record(self.zone_sublocation1),
            )

    def test_prepare_unload_buffer_empty(self):
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={},
        )
        # check response
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            self.zone_location,
            self.picking_type,
            move_lines,
        )

    def test_prepare_unload_buffer_one_line(self):
        # scan a destination package to get something in the buffer
        move_line = self.picking1.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
            },
        )
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={},
        )
        # check response
        self.assert_response_unload_set_destination(
            response,
            self.zone_location,
            self.picking_type,
            move_line,
        )

    def test_prepare_unload_buffer_multi_line_same_destination(self):
        # scan a destination package for some move lines
        # to get several lines in the buffer (which have the same destination)
        self.another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        move_lines = self.picking5.move_line_ids
        self.assertEqual(move_lines.location_dest_id, self.packing_location)
        for move_line, package_dest in zip(
            move_lines, self.free_package | self.another_package
        ):
            self.service.dispatch(
                "set_destination",
                params={
                    "move_line_id": move_line.id,
                    "barcode": package_dest.name,
                    "quantity": move_line.product_uom_qty,
                },
            )
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={},
        )
        # check response
        self.assert_response_unload_all(
            response,
            self.zone_location,
            self.picking_type,
            move_lines,
        )

    def test_list_move_lines_empty_location(self):
        response = self.service.dispatch(
            "list_move_lines",
            params={"order": "location"},
        )
        # TODO: order by location?
        move_lines = self.service._find_location_move_lines()
        self.assert_response_select_line(
            response,
            self.zone_location,
            self.picking_type,
            move_lines,
        )
        data_move_lines = response["data"]["select_line"]["move_lines"]
        # Check that the move line in "Zone sub-location 1" is about to empty
        # its location if we process it
        data_move_line = [
            m
            for m in data_move_lines
            if m["location_src"]["barcode"] == "ZONE_SUBLOCATION_1"
        ][0]
        self.assertTrue(data_move_line["location_will_be_empty"])
        # Same check with the internal method
        move_line = self.env["stock.move.line"].browse(data_move_line["id"])
        location_src = move_line.location_id
        move_line_will_empty_location = location_src.planned_qty_in_location_is_empty(
            move_lines=move_line
        )
        self.assertTrue(move_line_will_empty_location)
        # But if we check the location without giving the move line as parameter,
        # knowing that this move line hasn't its 'qty_done' field filled,
        # the location won't be considered empty with such pending move line
        move_line_will_empty_location = location_src.planned_qty_in_location_is_empty()
        self.assertFalse(move_line_will_empty_location)
