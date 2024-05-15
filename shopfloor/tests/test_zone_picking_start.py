# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_zone_picking_base import ZonePickingCommonCase

# pylint: disable=missing-return


class ZonePickingStartCase(ZonePickingCommonCase):
    """Tests for endpoint used from start

    * /scan_location

    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # create a picking w/ a different picking type
        # which should be excluded from picking types list
        bad_picking_type = cls.picking_type.sudo().copy(
            {
                "name": "Bad type",
                "sequence_code": "WH/BAD",
                "default_location_src_id": cls.zone_location.id,
                "shopfloor_menu_ids": False,
            }
        )
        cls.extra_picking = extra_picking = cls._create_picking(
            lines=[(cls.product_b, 10)],
            picking_type=bad_picking_type,
        )
        cls._fill_stock_for_moves(
            extra_picking.move_ids, in_package=True, location=cls.zone_sublocation1
        )
        cls._update_qty_in_location(cls.zone_sublocation1, cls.product_b, 10)
        extra_picking.action_assign()

    def test_data_for_zone(self):
        op_type_data = self.data.picking_type(self.menu.picking_type_ids[0])
        zones_data = self.service._response_for_start()["data"]["start"]["zones"]
        expected_sub1 = dict(
            self.data.location(self.zone_sublocation1),
            lines_count=1,
            picking_count=1,
            priority_lines_count=0,
            priority_picking_count=0,
            operation_types=[
                dict(
                    op_type_data,
                    lines_count=1,
                    picking_count=1,
                    priority_lines_count=0,
                    priority_picking_count=0,
                )
            ],
        )
        expected_sub2 = dict(
            self.data.location(self.zone_sublocation2),
            lines_count=2,
            picking_count=1,
            priority_lines_count=0,
            priority_picking_count=0,
            operation_types=[
                dict(
                    op_type_data,
                    lines_count=2,
                    picking_count=1,
                    priority_lines_count=0,
                    priority_picking_count=0,
                )
            ],
        )
        expected_sub3 = dict(
            self.data.location(self.zone_sublocation3),
            lines_count=2,
            picking_count=2,
            priority_lines_count=0,
            priority_picking_count=0,
            operation_types=[
                dict(
                    op_type_data,
                    lines_count=2,
                    picking_count=2,
                    priority_lines_count=0,
                    priority_picking_count=0,
                )
            ],
        )
        expected_sub4 = dict(
            self.data.location(self.zone_sublocation4),
            lines_count=3,
            picking_count=2,
            priority_lines_count=0,
            priority_picking_count=0,
            operation_types=[
                dict(
                    op_type_data,
                    lines_count=3,
                    picking_count=2,
                    priority_lines_count=0,
                    priority_picking_count=0,
                )
            ],
        )
        expected_sub5 = dict(
            self.data.location(self.zone_sublocation5),
            lines_count=2,
            picking_count=1,
            priority_lines_count=0,
            priority_picking_count=0,
            operation_types=[
                dict(
                    op_type_data,
                    lines_count=2,
                    picking_count=1,
                    priority_lines_count=0,
                    priority_picking_count=0,
                )
            ],
        )
        self.assertEqual(
            zones_data,
            [expected_sub1, expected_sub2, expected_sub3, expected_sub4, expected_sub5],
        )

    def test_select_zone(self):
        """Scanned location invalid, no location found."""
        response = self.service.dispatch("select_zone")
        self.assert_response_start(response)

    def test_select_zone_with_loaded_buffer(self):
        """Check loaded buffer info in select zone answer."""
        zone_location = self.zone_location
        picking_type = self.picking1.picking_type_id
        move_line = self.picking5.move_line_ids[1]
        # change the destination location on the move line
        move_line.location_dest_id = self.zone_sublocation3
        # and set the destination package
        self.service._set_destination_package(
            move_line,
            move_line.reserved_uom_qty,
            self.free_package,
        )
        response = self.service.dispatch("select_zone")
        data = {
            "zones": self.service._data_for_select_zone(zone_location.child_ids),
            "buffer": {
                "zone_location": self.service.data.location(zone_location),
                "picking_type": self.service.data.picking_type(picking_type),
            },
        }
        self.assert_response(
            response,
            next_state="start",
            data=data,
        )

    def test_scan_location_wrong_barcode(self):
        """Scanned location invalid, no location found."""
        response = self.service.dispatch(
            "scan_location",
            params={"barcode": "UNKNOWN LOCATION"},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.no_location_found(),
        )

    def test_scan_location_not_allowed(self):
        """Scanned location not allowed because it's not a child of picking
        types' source location.
        """
        response = self.service.dispatch(
            "scan_location",
            params={"barcode": self.customer_location.barcode},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_not_allowed(),
        )

    def test_scan_location_no_move_lines(self):
        """Scanned location valid, but no move lines found in it."""
        sub1_lines = self.service._find_location_move_lines(self.zone_sublocation1)
        # no more lines available
        sub1_lines.picking_id.action_cancel()
        response = self.service.dispatch(
            "scan_location",
            params={"barcode": self.zone_sublocation1.barcode},
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.no_lines_to_process(),
        )

    def test_scan_location_ok(self):
        """Scanned location valid, list of picking types of related move lines."""
        response = self.service.dispatch(
            "scan_location",
            params={"barcode": self.zone_location.barcode},
        )
        self.assert_response_select_picking_type(
            response,
            zone_location=self.zone_location,
            picking_types=self.picking_type,
        )
