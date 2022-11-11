# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_location_content_transfer_base import LocationContentTransferCommonCase


class TestLocationContentTransferStart(LocationContentTransferCommonCase):
    """Tests for start state and recover

    Endpoints:

    * /start_or_recover
    * /scan_location
    """

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        products = cls.product_a + cls.product_b + cls.product_c + cls.product_d
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        cls.picking1 = picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = picking2 = cls._create_picking(
            lines=[(cls.product_c, 10), (cls.product_d, 10)]
        )
        cls.pickings = picking1 | picking2

        cls.content_loc2 = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Content Location 2",
                    "barcode": "Content2",
                    "location_id": cls.picking_type.default_location_src_id.id,
                }
            )
        )
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_lines[0], location=cls.content_loc)
        cls._fill_stock_for_moves(picking2.move_lines[1], location=cls.content_loc2)
        cls.pickings.action_assign()
        cls.move_lines = cls.pickings.move_line_ids

    def test_start_fresh(self):
        """Start a fresh session when there is no transfer to recover"""
        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response(response, next_state="scan_location")

    def test_start_recover_destination_all(self):
        """Recover transfers, all move lines have the same destination"""
        self._simulate_pickings_selected(self.picking1)
        # all lines go to the same destination (shelf1)
        self.assertEqual(len(self.picking1.mapped("move_line_ids.location_dest_id")), 1)

        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response_scan_destination_all(
            response,
            self.picking1,
            message=self.service.msg_store.recovered_previous_session(),
        )

    def test_start_recover_destination_single(self):
        """Recover transfers, at least one move line has a different destination"""
        self._simulate_pickings_selected(self.pickings)
        self.picking1.package_level_ids.location_dest_id = self.shelf2
        # we have different destinations
        self.assertEqual(len(self.pickings.mapped("move_line_ids.location_dest_id")), 2)
        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response_start_single(
            response,
            self.pickings,
            message=self.service.msg_store.recovered_previous_session(),
        )

    def test_scan_location_not_found(self):
        """Scan a location with content to transfer, barcode not found"""
        response = self.service.dispatch(
            "scan_location", params={"barcode": "NOT_FOUND"}
        )
        self.assert_response_start(
            response, message=self.service.msg_store.barcode_not_found()
        )

    def test_scan_location_find_content_destination_all(self):
        """Scan a location with content to transfer, all dest. identical"""
        # all lines go to the same destination (shelf1)
        self.assertEqual(len(self.move_lines.location_dest_id), 1)
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        processed_move_lines = self.move_lines.filtered(
            lambda line: line.location_id == self.content_loc
        )
        processed_pickings = processed_move_lines.picking_id
        self.assertTrue(processed_pickings != self.pickings)
        self.assert_response_scan_destination_all(response, processed_pickings)
        self.assertRecordValues(
            processed_pickings, [{"user_id": self.env.uid}, {"user_id": self.env.uid}]
        )
        self.assertRecordValues(
            processed_move_lines,
            [
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
            ],
        )
        self.assertRecordValues(
            processed_pickings.package_level_ids, [{"is_done": True}]
        )

    def test_scan_location_find_content_destination_single(self):
        """Scan a location with content to transfer, different destinations"""
        self.picking1.package_level_ids.location_dest_id = self.shelf2
        # we have different destinations
        self.assertEqual(len(self.pickings.mapped("move_line_ids.location_dest_id")), 2)
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        processed_move_lines = self.move_lines.filtered(
            lambda line: line.location_id == self.content_loc
        )
        processed_pickings = processed_move_lines.picking_id
        self.assert_response_start_single(response, processed_pickings)
        self.assertRecordValues(
            processed_pickings, [{"user_id": self.env.uid}, {"user_id": self.env.uid}]
        )
        self.assertRecordValues(
            processed_move_lines,
            [
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
            ],
        )
        self.assertRecordValues(
            processed_pickings.package_level_ids, [{"is_done": True}]
        )

    def test_scan_location_different_picking_type(self):
        """Content has different picking types, can't move"""
        picking_other_type = self._create_picking(
            picking_type=self.wh.pick_type_id, lines=[(self.product_a, 10)]
        )
        self._fill_stock_for_moves(
            picking_other_type.move_lines, location=self.content_loc
        )
        picking_other_type.action_assign()

        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_start(
            response,
            message={
                "message_type": "error",
                "body": "This location content can't be moved at once.",
            },
        )


class LocationContentTransferStartSpecialCase(LocationContentTransferCommonCase):
    """Tests for start state and recover (special cases without setup)

    Endpoints:

    * /start_or_recover
    * /scan_location
    """

    def test_scan_location_wrong_picking_type_error(self):
        """Content has different picking type than menu"""
        picking = self._create_picking(
            picking_type=self.wh.pick_type_id,
            lines=[(self.product_a, 10), (self.product_b, 10)],
        )
        self._fill_stock_for_moves(
            picking.move_lines, in_package=True, location=self.content_loc
        )
        picking.action_assign()
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_start(
            response,
            message={
                "message_type": "error",
                "body": "You cannot move this using this menu.",
            },
        )

    def test_scan_location_wrong_picking_type_allow_unreserve_ok(self):
        """Content has different picking type than menu, option to unreserve

        The content must be unreserved, new moves created and the previous
        content re-reserved.
        """
        self.menu.sudo().allow_unreserve_other_moves = True

        picking = self._create_picking(
            picking_type=self.wh.pick_type_id,
            lines=[(self.product_a, 10), (self.product_b, 10)],
        )
        self._fill_stock_for_moves(
            picking.move_lines, in_package=True, location=self.content_loc
        )
        picking.action_assign()
        # place goods in shelf1 to ensure the original picking can take goods here
        other_pack_a = self.env["stock.quant.package"].create({})
        other_pack_b = self.env["stock.quant.package"].create({})
        self._update_qty_in_location(
            self.shelf1, self.product_a, 10, package=other_pack_a
        )
        self._update_qty_in_location(
            self.shelf1, self.product_b, 10, package=other_pack_b
        )
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        new_picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", self.picking_type.id)]
        )
        self.assertEqual(len(new_picking), 1)
        self.assert_response_scan_destination_all(response, new_picking)
        self.assertRecordValues(new_picking, [{"user_id": self.env.uid}])
        self.assertRecordValues(
            new_picking.move_line_ids,
            [{"qty_done": 10.0}, {"qty_done": 10.0}],
        )
        self.assertRecordValues(new_picking.package_level_ids, [{"is_done": True}])

        # the original picking must be reserved again, should have taken the goods
        # of shelf1
        self.assertRecordValues(
            picking.move_line_ids,
            [
                {
                    "qty_done": 0.0,
                    "location_id": self.shelf1.id,
                    "package_id": other_pack_a.id,
                },
                {
                    "qty_done": 0.0,
                    "location_id": self.shelf1.id,
                    "package_id": other_pack_b.id,
                },
            ],
        )

    def test_scan_location_wrong_picking_type_allow_unreserve_empty(self):
        """Content has different picking type than menu, option to unreserve

        There is no move line of another picking type to unreserve.
        """
        self.menu.sudo().allow_unreserve_other_moves = True
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_empty(self.content_loc),
        )

    def test_scan_location_wrong_picking_type_allow_unreserve_error(self):
        """Content has different picking type than menu, option to unreserve

        If quantity has been partially picked on the existing transfer, prevent
        to unreserve them.
        """
        self.menu.sudo().allow_unreserve_other_moves = True

        picking = self._create_picking(
            picking_type=self.wh.pick_type_id,
            lines=[(self.product_a, 10), (self.product_b, 10)],
        )
        self._fill_stock_for_moves(
            picking.move_lines, in_package=True, location=self.content_loc
        )
        picking.action_assign()
        # a user picked qty
        picking.move_line_ids[0].qty_done = 10
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.picking_already_started_in_location(picking),
        )
        # check that the original moves are still assigned
        self.assertRecordValues(
            picking.move_lines, [{"state": "assigned"}, {"state": "assigned"}]
        )

    def test_scan_location_create_moves(self):
        """The scanned location has no move lines but has some quants to move."""
        picking_type = self.menu.picking_type_ids
        # product_a alone
        self.env["stock.quant"]._update_available_quantity(
            self.product_a,
            self.content_loc,
            10,
        )
        # product_b in a package
        package = self.env["stock.quant.package"].create({})
        self.env["stock.quant"]._update_available_quantity(
            self.product_b, self.content_loc, 10, package_id=package
        )
        # product_c & product_d in a package
        package2 = self.env["stock.quant.package"].create({})
        self.env["stock.quant"]._update_available_quantity(
            self.product_c, self.content_loc, 5, package_id=package2
        )
        self.env["stock.quant"]._update_available_quantity(
            self.product_d, self.content_loc, 5, package_id=package2
        )
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        picking = self.env["stock.picking"].search(
            [("picking_type_id", "=", picking_type.id)]
        )
        self.assertEqual(len(picking), 1)
        self.assert_response_scan_destination_all(response, picking)
        move_line_id = response["data"]["scan_destination_all"]["move_lines"][0]["id"]
        package_levels = response["data"]["scan_destination_all"]["package_levels"]
        self.assertIn(move_line_id, picking.move_line_ids.ids)
        self.assertEqual(package_levels[0]["id"], picking.package_level_ids[0].id)
        self.assertEqual(package_levels[0]["package_src"]["id"], package.id)
        self.assertEqual(package_levels[1]["id"], picking.package_level_ids[1].id)
        self.assertEqual(package_levels[1]["package_src"]["id"], package2.id)
        # product_a in a move line without package
        self.assertEqual(
            picking.move_line_ids_without_package.mapped("product_id"), self.product_a
        )
        # all other products are in package levels
        self.assertEqual(
            picking.package_level_ids.mapped("package_id.quant_ids.product_id"),
            self.product_b | self.product_c | self.product_d,
        )
        # all products are in move lines
        self.assertEqual(
            picking.move_line_ids.mapped("product_id"),
            self.product_a | self.product_b | self.product_c | self.product_d,
        )
        self.assertEqual(picking.state, "assigned")
