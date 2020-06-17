from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferStartCase(LocationContentTransferCommonCase):
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
        cls._fill_stock_for_moves(
            picking1.move_lines, in_package=True, location=cls.content_loc
        )
        cls._fill_stock_for_moves(picking2.move_lines, location=cls.content_loc)
        cls.pickings.action_assign()

    def test_start_fresh(self):
        """Start a fresh session when there is no transfer to recover"""
        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response(response, next_state="start")

    def test_start_recover_destination_all(self):
        """Recover transfers, all move lines have the same destination"""
        self._simulate_pickings_selected(self.pickings)
        # all lines go to the same destination (shelf1)
        self.assertEqual(len(self.pickings.mapped("move_line_ids.location_dest_id")), 1)

        response = self.service.dispatch("start_or_recover", params={})
        self.assert_response_scan_destination_all(
            response,
            self.pickings,
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
        self.assertEqual(len(self.pickings.mapped("move_line_ids.location_dest_id")), 1)
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_scan_destination_all(response, self.pickings)
        self.assertRecordValues(
            self.pickings, [{"user_id": self.env.uid}, {"user_id": self.env.uid}]
        )
        self.assertRecordValues(
            self.pickings.move_line_ids,
            [
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
            ],
        )
        self.assertRecordValues(self.picking1.package_level_ids, [{"is_done": True}])

    def test_scan_location_find_content_destination_single(self):
        """Scan a location with content to transfer, different destinations"""
        self.picking1.package_level_ids.location_dest_id = self.shelf2
        # we have different destinations
        self.assertEqual(len(self.pickings.mapped("move_line_ids.location_dest_id")), 2)
        response = self.service.dispatch(
            "scan_location", params={"barcode": self.content_loc.barcode}
        )
        self.assert_response_start_single(response, self.pickings)
        self.assertRecordValues(
            self.pickings, [{"user_id": self.env.uid}, {"user_id": self.env.uid}]
        )
        self.assertRecordValues(
            self.pickings.move_line_ids,
            [
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
                {"qty_done": 10.0},
            ],
        )
        self.assertRecordValues(self.picking1.package_level_ids, [{"is_done": True}])

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

    def test_scan_location_wrong_picking_type(self):
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
                "body": "This location content can't be moved using this menu.",
            },
        )
