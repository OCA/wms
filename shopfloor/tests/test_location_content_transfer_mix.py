# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_location_content_transfer_base import LocationContentTransferCommonCase

# pylint: disable=missing-return


class LocationContentTransferMixCase(LocationContentTransferCommonCase):
    """Tests where we mix location content transfer with other scenarios."""

    @classmethod
    def setUpClassUsers(cls):
        super().setUpClassUsers()
        Users = (
            cls.env["res.users"]
            .sudo()
            .with_context(
                **{"no_reset_password": True, "mail_create_nosubscribe": True}
            )
        )
        cls.stock_user2 = Users.create(
            {
                "name": "Paul Posichon",
                "login": "paulposichon",
                "email": "paul.posichon@example.com",
                "notification_type": "inbox",
                "groups_id": [(6, 0, [cls.env.ref("stock.group_stock_user").id])],
            }
        )

    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.zp_menu = cls.env.ref("shopfloor.shopfloor_menu_demo_zone_picking")
        cls.wh.sudo().delivery_steps = "pick_pack_ship"
        cls.pack_location = cls.wh.wh_pack_stock_loc_id
        cls.ship_location = cls.wh.wh_output_stock_loc_id
        # Allows zone picking to process PICK picking type
        cls.zp_menu.sudo().picking_type_ids += cls.wh.pick_type_id
        # Allows location content transfer to process PACK picking type
        cls.menu.sudo().picking_type_ids = cls.wh.pack_type_id
        cls.wh.pack_type_id.sudo().default_location_dest_id = cls.env.ref(
            "stock.stock_location_output"
        )

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.packing_location.sudo().active = True
        products = cls.product_a
        for product in products:
            cls.env["stock.putaway.rule"].sudo().create(
                {
                    "product_id": product.id,
                    "location_in_id": cls.stock_location.id,
                    "location_out_id": cls.shelf1.id,
                }
            )

        # Put product_a quantities in different packages to get
        # two stock move lines (6 and 4 to satisfy 10 qties)
        cls.package_1 = cls.env["stock.quant.package"].create({"name": "PACKAGE_1"})
        cls.package_2 = cls.env["stock.quant.package"].create({"name": "PACKAGE_2"})
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 6, package=cls.package_1
        )
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 4, package=cls.package_2
        )
        # Create the pick/pack/ship transfers
        cls.ship_move_a = cls.env["stock.move"].create(
            {
                "name": cls.product_a.display_name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 10.0,
                "product_uom": cls.product_a.uom_id.id,
                "location_id": cls.ship_location.id,
                "location_dest_id": cls.customer_location.id,
                "warehouse_id": cls.wh.id,
                "picking_type_id": cls.wh.out_type_id.id,
                "procure_method": "make_to_order",
                "state": "draft",
            }
        )
        cls.ship_move_a._assign_picking()
        cls.ship_move_a._action_confirm()
        cls.pack_move_a = cls.ship_move_a.move_orig_ids[0]
        cls.pick_move_a = cls.pack_move_a.move_orig_ids[0]
        cls.picking1 = cls.pick_move_a.picking_id
        cls.packing1 = cls.pack_move_a.picking_id
        cls.picking1.action_assign()

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.zp_menu, profile=self.profile) as work:
            self.zp_service = work.component(usage="zone_picking")

    def _zone_picking_process_line(self, move_line, dest_location=None):
        picking = move_line.picking_id
        zone_location = picking.location_id
        picking_type = picking.picking_type_id
        self.zp_service.work.current_zone_location = zone_location
        self.zp_service.work.current_picking_type = picking_type
        move_lines = picking.move_line_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        # Select the picking type
        response = self.zp_service.scan_location(barcode=zone_location.barcode)
        available_picking_type_ids = [
            r["id"] for r in response["data"]["select_picking_type"]["picking_types"]
        ]
        assert picking_type.id in available_picking_type_ids
        assert "message" not in response
        # Check the move lines related to the picking type
        response = self.zp_service.list_move_lines()
        available_move_line_ids = [
            r["id"] for r in response["data"]["select_line"]["move_lines"]
        ]
        assert not set(move_lines.ids) - set(available_move_line_ids)
        assert "message" not in response
        # Set the destination on the move line
        if not dest_location:
            dest_location = move_line.location_dest_id
        qty = move_line.reserved_uom_qty
        response = self.zp_service.set_destination(
            move_line.id,
            dest_location.barcode,
            qty,
            confirmation=True,
        )
        assert response["message"]["message_type"] == "success"
        self.assertEqual(move_line.state, "done")
        self.assertEqual(move_line.move_id.product_uom_qty, qty)

    def _location_content_transfer_process_line(
        self, move_line, set_destination=False, user=None
    ):
        service = self.service
        if user:
            env = self.env(user=user)
            service = self.get_service(
                "location_content_transfer",
                env=env,
                menu=self.menu,
                profile=self.profile,
            )

        pack_location = move_line.location_id
        out_location = move_line.location_dest_id
        # Scan the location
        response = service.scan_location(pack_location.barcode)
        # Set the destination
        if set_destination:
            assert response["next_state"] in ("scan_destination_all", "start_single")
            qty = move_line.reserved_uom_qty
            if response["next_state"] == "scan_destination_all":
                response = service.set_destination_all(
                    pack_location.id, out_location.barcode
                )
                self.assert_response_start(
                    response,
                    message=service.msg_store.location_content_transfer_complete(
                        pack_location,
                        out_location,
                    ),
                )
                self.assertEqual(move_line.state, "done")
                self.assertEqual(move_line.move_id.product_uom_qty, qty)
            elif response["next_state"] == "start_single":
                response = service.scan_line(
                    pack_location.id, move_line.id, move_line.product_id.barcode
                )
                assert response["message"]["message_type"] == "success"
                response = service.set_destination_line(
                    pack_location.id, move_line.id, qty, out_location.barcode
                )
                assert response["message"]["message_type"] == "success"
                assert move_line.state == "done"
                assert move_line.qty_done == qty
        return response

    def test_with_zone_picking1(self):
        """Test the following scenario:

        1) Operator-1 processes the first pallet with the "zone picking" scenario:

            move1 PICK -> PACK 'done'

        2) Operator-2 with the "location content transfer" scenario scan
          the location where this first pallet is (so the move line is still not
          done, the operator is currently moving the goods to the destination location):

            move1 PACK -> SHIP 'assigned' while the operator is moving it

        3) Operator-1 process the second pallet with the "zone picking" scenario:

            move2 PICK -> PACK 'done'

        4) Operator-3 with the "location content transfer" scenario scan
          the location where this second pallet is, Odoo should return only this
          second pallet as the first one, even if not fully processed (done)
          is not physically available in the scanned location.

            move2 PACK -> SHIP 'assigned' is proposed to the operator
            move1 PACK -> SHIP while still 'assigned' is not proposed to the operator
        """
        picking = self.picking1
        move_lines = picking.move_line_ids
        pick_move_line1 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_1
        )
        pick_move_line2 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_2
        )
        # Operator-1 process the first pallet with the "zone picking" scenario
        self._zone_picking_process_line(pick_move_line1)
        # Operator-2 with the "location content transfer" scenario scan
        # the location where this first pallet is (so the move line is still not
        # done, the operator is currently moving the goods to the destination location)
        pack_move_line1 = pick_move_line1.move_id.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        ).move_line_ids.filtered(lambda l: not l.shopfloor_user_id)
        self._location_content_transfer_process_line(pack_move_line1)
        # Operator-1 process the second pallet with the "zone picking" scenario
        self._zone_picking_process_line(pick_move_line2)
        # Operator-3 with the "location content transfer" scenario scan
        # the location where this second pallet is
        pack_move_line2 = pick_move_line2.move_id.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        ).move_line_ids.filtered(lambda l: not l.shopfloor_user_id)
        assert (
            len(pack_move_line2) == 1
        ), "Operator-3 should end up with one move line taken from {}".format(
            pack_move_line2.picking_id.name
        )
        self._location_content_transfer_process_line(pack_move_line2)

    def test_with_zone_picking2(self):
        """Test the following scenario:

        1) Operator-1 processes the first pallet with the "zone picking" scenario
           to move the goods to PACK-1 and unload in destination location1:

            move1 PICK -> PACK-1 'done'

        2) Operator-1 processes the second pallet with the "zone picking" scenario
           to move the goods to PACK-2 and unload in destination location2:

            move1 PICK -> PACK-2 'done'

        3) Operator-2 with the "location content transfer" scenario scan
          the location where the first pallet is (PACK-1):
            - the app should found one move line
            - this move line will be put in its own transfer as its sibling lines
              are in another source location
            - as such the app should ask the destination location (as there is
              only one line)

            move1 PACK-2 -> SHIP (still handled by the operator so not 'done')

        4) Operator-3 with the "location content transfer" scenario scan
          the location where the first pallet is (PACK-1):
            - nothing is found as the pallet is currently handled by Operator-2

        5) If Operator-2 is unable to finish the flow with the first pallet
          (barcode device out of battery... etc), he should be able to recover
          what he started.

        6) Operator-2 then finishes its operation regarding the first pallet, and
          scan the location where the second pallet is (PACK-2). He should find
          only this pallet available.
        """
        move_lines = self.picking1.move_line_ids
        pick_move_line1 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_1
        )
        pick_move_line2 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_2
        )
        # Operator-1 process the first pallet with the "zone picking" scenario
        orig_dest_location = pick_move_line1.location_dest_id
        dest_location1 = pick_move_line1.location_dest_id.sudo().copy(
            {
                "name": orig_dest_location.name + "_1",
                "barcode": orig_dest_location.barcode + "_1",
                "location_id": orig_dest_location.id,
            }
        )
        self._zone_picking_process_line(pick_move_line1, dest_location=dest_location1)
        # Operator-1 process the second pallet with the "zone picking" scenario
        dest_location2 = orig_dest_location.sudo().copy(
            {
                "name": orig_dest_location.name + "_2",
                "barcode": orig_dest_location.barcode + "_2",
                "location_id": orig_dest_location.id,
            }
        )
        self._zone_picking_process_line(pick_move_line2, dest_location=dest_location2)
        pack_move_a = pick_move_line1.move_id.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        self.assertEqual(pack_move_a, self.pack_move_a)
        pack_first_pallet = pack_move_a.move_line_ids.filtered(
            lambda l: not l.shopfloor_user_id and l.location_id == dest_location1
        )
        self.assertEqual(pack_first_pallet.reserved_uom_qty, 6)
        self.assertEqual(pack_first_pallet.qty_done, 0)
        pack_second_pallet = pack_move_a.move_line_ids.filtered(
            lambda l: not l.shopfloor_user_id and l.location_id == dest_location2
        )
        self.assertEqual(pack_second_pallet.reserved_uom_qty, 4)
        self.assertEqual(pack_second_pallet.qty_done, 0)
        # Operator-2 with the "location content transfer" scenario scan
        # the location where the first pallet is.
        # This pallet/move line will be put in its own transfer as its sibling
        # lines are in another source location.
        previous_picking = pack_first_pallet.picking_id
        response = self._location_content_transfer_process_line(pack_first_pallet)
        new_picking = pack_first_pallet.picking_id
        self.assertTrue(previous_picking != new_picking)
        self.assert_response_scan_destination_all(response, new_picking)
        response_packages = response["data"]["scan_destination_all"]["package_levels"]
        self.assertEqual(len(response_packages), 1)
        self.assertEqual(
            response_packages[0]["package_src"]["id"], pack_first_pallet.package_id.id
        )
        # Ensure that the second pallet is untouched
        self.assertEqual(pack_second_pallet.qty_done, 0)
        # Operator-3 with the "location content transfer" scenario scan
        # the location where the first pallet is: he should found nothing
        response = self._location_content_transfer_process_line(
            pack_first_pallet, user=self.stock_user2
        )
        self.assert_response_start(
            response, message=self.service.msg_store.new_move_lines_not_assigned()
        )
        # Check if Operator-2 is able to recover its session
        expected_picking = pack_first_pallet.picking_id
        response = self.service.start_or_recover()
        self.assert_response_scan_destination_all(
            response,
            expected_picking,
            message=self.service.msg_store.recovered_previous_session(),
        )
        # Operator-2 finishes its operation regarding the first pallet
        qty = pack_first_pallet.reserved_uom_qty
        response = self.service.set_destination_all(
            pack_first_pallet.location_id.id, pack_first_pallet.location_dest_id.barcode
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_content_transfer_complete(
                pack_first_pallet.location_id,
                pack_first_pallet.location_dest_id,
            ),
        )
        self.assertEqual(pack_first_pallet.qty_done, 6)
        self.assertEqual(pack_first_pallet.state, "done")
        self.assertEqual(pack_first_pallet.move_id.product_uom_qty, qty)
        # Ensure that the second pallet is untouched
        self.assertEqual(pack_second_pallet.qty_done, 0)
        # Operator-2 (still with the "location content transfer" scenario) scan
        # the location where the second pallet is
        pack_move_a = pick_move_line2.move_id.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        )
        self.assertEqual(pack_move_a, self.pack_move_a)
        pack_second_pallet = pack_move_a.move_line_ids.filtered(
            lambda l: not l.shopfloor_user_id and l.location_id == dest_location2
        )
        picking_before = pack_second_pallet.picking_id
        move_lines = self.service.search_move_line.search_move_lines(
            locations=pack_second_pallet.location_id
        )
        response = self._location_content_transfer_process_line(pack_second_pallet)
        response_packages = response["data"]["scan_destination_all"]["package_levels"]
        self.assertEqual(len(response_packages), 1)
        self.assertEqual(
            response_packages[0]["package_src"]["id"], pack_second_pallet.package_id.id
        )
        picking_after = pack_second_pallet.picking_id
        self.assertEqual(picking_before, picking_after)
        self.assert_response_scan_destination_all(response, picking_after)

    def test_with_zone_picking3(self):
        """Test the following scenario:

        1) Operator-1 processes the first pallet with the "zone picking" scenario
           to move the goods to PACK-1:

            move1 PICK -> PACK-1 'done'

        2) Operator-2 with the "location content transfer" scenario scan
          the location where the first pallet is (PACK-1):
            - the app should found one move line
            - this move line will be put in its own transfer in any case
            - as such the app should ask the destination location (as there is
              only one line)

            move1 PACK-1 -> SHIP (still handled by the operator so not 'done')

        3) Operator-1 processes the second pallet with the "zone picking" scenario
           to move the goods to PACK-2:

            move1 PICK -> PACK-2 'done'

            - this will automatically update the reservation (new move line) in
              the transfer previously processed by Operator-2.

        4) Operator-2 then finishes its operation regarding the first pallet
          without any trouble.

        5) Operator-2 with the "location content transfer" scenario scan
          the location where the second pallet is (PACK-2), etc
        """
        move_lines = self.picking1.move_line_ids
        pick_move_line1 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_1
        )
        pick_move_line2 = move_lines.filtered(
            lambda ml: ml.result_package_id == self.package_2
        )
        orig_dest_location = pick_move_line1.location_dest_id
        dest_location1 = pick_move_line1.location_dest_id.sudo().copy(
            {
                "name": orig_dest_location.name + "_1",
                "barcode": orig_dest_location.barcode + "_1",
                "location_id": orig_dest_location.id,
            }
        )
        dest_location2 = orig_dest_location.sudo().copy(
            {
                "name": orig_dest_location.name + "_2",
                "barcode": orig_dest_location.barcode + "_2",
                "location_id": orig_dest_location.id,
            }
        )
        # Operator-1 process the first pallet with the "zone picking" scenario
        self._zone_picking_process_line(pick_move_line1, dest_location=dest_location1)
        pack_move_a1 = pick_move_line1.move_id.move_dest_ids.filtered(
            lambda m: m.move_line_ids.package_id == self.package_1
        )
        self.assertEqual(pack_move_a1, self.pack_move_a)
        pack_first_pallet = pack_move_a1.move_line_ids.filtered(
            lambda l: not l.shopfloor_user_id and l.location_id == dest_location1
        )
        self.assertEqual(pack_first_pallet.reserved_uom_qty, 6)
        self.assertEqual(pack_first_pallet.qty_done, 0)
        # Operator-2 with the "location content transfer" scenario scan
        # the location where the first pallet is.
        # This pallet/move line will be put in its own move and transfer by convenience
        original_pack_transfer = pack_first_pallet.picking_id
        response = self._location_content_transfer_process_line(pack_first_pallet)
        new_pack_transfer = pack_first_pallet.picking_id
        self.assertNotEqual(original_pack_transfer, new_pack_transfer)
        self.assert_response_scan_destination_all(response, new_pack_transfer)
        response_packages = response["data"]["scan_destination_all"]["package_levels"]
        self.assertEqual(len(response_packages), 1)
        self.assertEqual(
            response_packages[0]["package_src"]["id"], pack_first_pallet.package_id.id
        )
        # All pack lines have been processed until now, so the existing pack
        # operation is now waiting goods from pick operation
        self.assertEqual(original_pack_transfer.state, "waiting")
        # Operator-1 process the second pallet with the "zone picking" scenario
        self._zone_picking_process_line(pick_move_line2, dest_location=dest_location2)
        pack_move_a2 = pick_move_line2.move_id.move_dest_ids.filtered(
            lambda m: m.move_line_ids.package_id == self.package_2
        )
        pack_second_pallet = pack_move_a2.move_line_ids.filtered(
            lambda l: not l.shopfloor_user_id and l.location_id == dest_location2
        )
        self.assertEqual(pack_second_pallet.reserved_uom_qty, 4)
        self.assertEqual(pack_second_pallet.qty_done, 0)
        # The last action has updated the pack operation (new move line) in the
        # transfer previously processed by Operator-2.
        self.assertEqual(original_pack_transfer.state, "assigned")
        self.assertIn(self.package_2, original_pack_transfer.move_line_ids.package_id)
        # Operator-2 finishes its operation regarding the first pallet without
        # any trouble as the processed move line has been put in its own
        # move+transfer
        qty = pack_first_pallet.reserved_uom_qty
        response = self.service.set_destination_all(
            pack_first_pallet.location_id.id, pack_first_pallet.location_dest_id.barcode
        )
        self.assert_response_start(
            response,
            message=self.service.msg_store.location_content_transfer_complete(
                pack_first_pallet.location_id,
                pack_first_pallet.location_dest_id,
            ),
        )
        self.assertEqual(pack_first_pallet.qty_done, 6)
        self.assertEqual(pack_first_pallet.state, "done")
        self.assertEqual(pack_first_pallet.move_id.product_uom_qty, qty)
        # Operator-2 with the "location content transfer" scenario scan
        # the location where the second pallet is.
        original_pack_transfer = pack_second_pallet.picking_id
        response = self._location_content_transfer_process_line(pack_second_pallet)
        new_pack_transfer = pack_second_pallet.picking_id
        # Transfer hasn't been split as we were processing the last line/pallet
        self.assertEqual(original_pack_transfer, new_pack_transfer)
        self.assert_response_scan_destination_all(response, new_pack_transfer)
        response_packages = response["data"]["scan_destination_all"]["package_levels"]
        self.assertEqual(len(response_packages), 1)
        self.assertEqual(
            response_packages[0]["package_src"]["id"], pack_second_pallet.package_id.id
        )
