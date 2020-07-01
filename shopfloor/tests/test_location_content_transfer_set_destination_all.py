from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferSetDestinationAllCase(LocationContentTransferCommonCase):
    """Tests for endpoint used from scan_destination_all

    * /set_destination_all
    * /go_to_single

    """

    # TODO see what can be common
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
        cls._simulate_pickings_selected(cls.pickings)

    def assert_all_done(self, destination):
        self.assertRecordValues(self.pickings, [{"state": "done"}, {"state": "done"}])
        self.assertRecordValues(
            self.pickings.move_line_ids,
            [
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
                {"qty_done": 10.0, "state": "done", "location_dest_id": destination.id},
            ],
        )
        self.assertRecordValues(
            self.picking1.package_level_ids,
            [{"is_done": True, "state": "done", "location_dest_id": destination.id}],
        )

    def test_set_destination_all_dest_location_ok(self):
        """Scanned destination location valid, moves set to done accepted"""
        sub_shelf1 = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Sub Shelf 1",
                    "barcode": "subshelf1",
                    "location_id": self.shelf1.id,
                }
            )
        )
        response = self.service.dispatch(
            "set_destination_all",
            params={"location_id": self.content_loc.id, "barcode": sub_shelf1.barcode},
        )
        self.assert_response_start(
            response,
            message={
                "message_type": "success",
                "body": "Content transferred from {}.".format(self.content_loc.name),
            },
        )
        self.assert_all_done(sub_shelf1)

    def test_set_destination_all_dest_location_not_found(self):
        """Barcode scanned for destination location is not found"""
        response = self.service.dispatch(
            "set_destination_all",
            params={"location_id": self.content_loc.id, "barcode": "NOT_FOUND"},
        )
        self.assert_response_scan_destination_all(
            response, self.pickings, message=self.service.msg_store.barcode_not_found()
        )

    def test_set_destination_all_dest_location_need_confirm(self):
        """Scanned dest. location != child but in picking type location

        So it needs confirmation.
        """
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                # expected location was shelf1, but shelf2 is valid as still in the
                # picking type's default dest location, ask confirmation (second scan)
                # from the user
                "barcode": self.shelf2.barcode,
            },
        )
        self.assert_response_confirm_scan_destination_all(response, self.pickings)

    def test_set_destination_all_dest_location_confirmation(self):
        """Scanned dest. location != child but in picking type location: confirm

        use the confirmation flag to confirm
        """
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                # expected location was shelf1, but shelf2 is valid as still in the
                # picking type's default dest location, ask confirmation (second scan)
                # from the user
                "barcode": self.shelf2.barcode,
                "confirmation": True,
            },
        )
        self.assert_response_start(
            response,
            message={
                "message_type": "success",
                "body": "Content transferred from {}.".format(self.content_loc.name),
            },
        )
        self.assert_all_done(self.shelf2)

    def test_set_destination_all_dest_location_invalid(self):
        """The scanned destination location is not in the menu's picking types"""
        response = self.service.dispatch(
            "set_destination_all",
            params={
                "location_id": self.content_loc.id,
                "barcode": self.dispatch_location.barcode,
            },
        )
        self.assert_response_scan_destination_all(
            response,
            self.pickings,
            message=self.service.msg_store.dest_location_not_allowed(),
        )

    def test_go_to_single(self):
        """User used to 'split by lines' button to process line per line"""
        response = self.service.dispatch(
            "go_to_single", params={"location_id": self.content_loc.id}
        )
        self.assert_response_start_single(response, self.pickings)


class LocationContentTransferSetDestinationAllSpecialCase(
    LocationContentTransferCommonCase
):
    """Tests for endpoint used from scan_destination_all (special cases without setup)

    * /set_destination_all
    * /go_to_single

    """

    def test_go_to_single_no_lines_to_process(self):
        """User used to 'split by lines' button to process line per line,
        but no lines to process.
        """
        response = self.service.dispatch(
            "go_to_single", params={"location_id": self.content_loc.id}
        )
        self.assert_response_start(
            response, message=self.service.msg_store.no_lines_to_process()
        )
