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

    def test_list_move_lines_order(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        self.zone_sublocation2.name = "AAA " + self.zone_sublocation2.name

        # Test by location
        today = fields.Datetime.today()
        future = fields.Datetime.add(
            fields.Datetime.end_of(fields.Datetime.today(), "day"), days=2
        )
        # change date to lines in the same location
        move1 = self.picking2.move_lines[0]
        move1.write({"date_expected": today})
        move1_line = move1.move_line_ids[0]
        move2 = self.picking2.move_lines[1]
        move2.write({"date_expected": future})
        move2_line = move2.move_line_ids[0]

        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="location"
        )
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertTrue(order_mapping[move1_line] < order_mapping[move2_line])

        # swap dates
        move2.write({"date_expected": today})
        move1.write({"date_expected": future})
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="location"
        )
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertTrue(order_mapping[move1_line] > order_mapping[move2_line])

        # Test by priority
        self.picking2.move_lines.write({"priority": "0"})
        (self.pickings - self.picking2).move_lines.write({"priority": "2"})
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="priority"
        )
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        # picking2 lines stay at the end as they are low priority
        # but move1_line comes before the other
        self.assertTrue(order_mapping[move1_line] > len(move_lines) - 4)
        self.assertTrue(order_mapping[move2_line] > len(move_lines) - 3)
        # swap dates again
        move2.write({"date_expected": future})
        move1.write({"date_expected": today})
        # and increase priority
        self.picking2.move_lines.write({"priority": "3"})
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="priority"
        )
        order_mapping = {line: i for i, line in enumerate(move_lines)}
        self.assertEqual(order_mapping[move1_line], 0)
        self.assertEqual(order_mapping[move2_line], 1)

    def test_list_move_lines_order_by_location(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "order": "location",
            },
        )
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="location"
        )
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )

    def test_list_move_lines_order_by_priority(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "order": "priority",
            },
        )
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="priority"
        )
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
        # first line done
        move_line.qty_done = move_line.product_uom_qty
        # get the next one
        response = self.service.dispatch(
            "scan_source",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "barcode": self.zone_sublocation1.barcode,
            },
        )
        move_line = new_picking.move_line_ids
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
            message=self.service.msg_store.several_products_in_location(
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
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        #   - scan source
        response = self.service.scan_source(
            zone_location.id, picking_type.id, self.zone_sublocation1.barcode,
        )
        move_line = self.picking1.move_line_ids
        self.assertEqual(response["next_state"], "set_line_destination")
        #   - set destination
        self.service.set_destination(
            zone_location.id,
            picking_type.id,
            move_line.id,
            self.free_package.name,
            move_line.product_uom_qty,
        )
        self.assertEqual(move_line.shopfloor_user_id, self.env.user)
        # The second user scans the same source location
        env = self.env(user=self.stock_user2)
        with self.work_on_services(
            env=env, menu=self.menu, profile=self.profile
        ) as work:
            service = work.component(usage="zone_picking")
            response = service.scan_source(
                zone_location.id, picking_type.id, self.zone_sublocation1.barcode,
            )
            self.assertEqual(response["next_state"], "select_line")
            self.assertEqual(
                response["message"],
                self.service.msg_store.location_empty(self.zone_sublocation1),
            )

    def test_prepare_unload_wrong_parameters(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "prepare_unload",
            params={
                "zone_location_id": 1234567890,
                "picking_type_id": picking_type.id,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )
        response = self.service.dispatch(
            "prepare_unload",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": 1234567890,
            },
        )
        self.assert_response_start(
            response, message=self.service.msg_store.record_not_found(),
        )

    def test_prepare_unload_buffer_empty(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        move_lines = self.service._find_location_move_lines(zone_location, picking_type)
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
        )

    def test_prepare_unload_buffer_one_line(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        # scan a destination package to get something in the buffer
        move_line = self.picking1.move_line_ids
        response = self.service.dispatch(
            "set_destination",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "move_line_id": move_line.id,
                "barcode": self.free_package.name,
                "quantity": move_line.product_uom_qty,
            },
        )
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        self.assert_response_unload_set_destination(
            response, zone_location, picking_type, move_line,
        )

    def test_prepare_unload_buffer_multi_line_same_destination(self):
        zone_location = self.zone_location
        picking_type = self.picking5.picking_type_id
        # scan a destination package for some move lines
        # to get several lines in the buffer (which have the same destination)
        self.another_package = self.env["stock.quant.package"].create(
            {"name": "ANOTHER_PACKAGE"}
        )
        self.assertEqual(
            self.picking5.move_line_ids.location_dest_id, self.packing_location
        )
        for move_line, package_dest in zip(
            self.picking5.move_line_ids, self.free_package | self.another_package
        ):
            self.service.dispatch(
                "set_destination",
                params={
                    "zone_location_id": zone_location.id,
                    "picking_type_id": picking_type.id,
                    "move_line_id": move_line.id,
                    "barcode": package_dest.name,
                    "quantity": move_line.product_uom_qty,
                },
            )
        # unload goods
        response = self.service.dispatch(
            "prepare_unload",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
            },
        )
        # check response
        self.assert_response_unload_all(
            response, zone_location, picking_type, self.picking5.move_line_ids,
        )

    def test_list_move_lines_empty_location(self):
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        response = self.service.dispatch(
            "list_move_lines",
            params={
                "zone_location_id": zone_location.id,
                "picking_type_id": picking_type.id,
                "order": "location",
            },
        )
        move_lines = self.service._find_location_move_lines(
            zone_location, picking_type, order="location"
        )
        self.assert_response_select_line(
            response, zone_location, picking_type, move_lines,
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
