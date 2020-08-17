from .test_location_content_transfer_base import LocationContentTransferCommonCase


class LocationContentTransferMixCase(LocationContentTransferCommonCase):
    """Tests where we mix location content transfer with other scenarios."""

    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.zp_menu = cls.env.ref("shopfloor.shopfloor_menu_zone_picking")
        cls.wh.sudo().delivery_steps = "pick_pack_ship"
        cls.pack_location = cls.wh.wh_pack_stock_loc_id
        cls.ship_location = cls.wh.wh_output_stock_loc_id
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
        cls.package_3 = cls.env["stock.quant.package"].create({"name": "PACKAGE_3"})
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 6, package=cls.package_1
        )
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 4, package=cls.package_2
        )
        cls._update_qty_in_location(
            cls.stock_location, cls.product_a, 5, package=cls.package_3
        )
        # Create the pick/pack/ship transfers
        cls.ship_move_a = cls.env["stock.move"].create(
            {
                "name": cls.product_a.display_name,
                "product_id": cls.product_a.id,
                "product_uom_qty": 15.0,
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
        cls.picking1.action_assign()

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.zp_menu, profile=self.profile) as work:
            self.zp_service = work.component(usage="zone_picking")

    def _zone_picking_process_line(self, move_line, dest_location=None):
        picking = move_line.picking_id
        zone_location = picking.location_id
        picking_type = picking.picking_type_id
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
        response = self.zp_service.list_move_lines(
            zone_location_id=zone_location.id,
            picking_type_id=picking_type.id,
            order="priority",
        )
        available_move_line_ids = [
            r["id"] for r in response["data"]["select_line"]["move_lines"]
        ]
        assert not set(move_lines.ids) - set(available_move_line_ids)
        assert "message" not in response
        # Set the destination on the move line
        if not dest_location:
            dest_location = move_line.location_dest_id
        qty = move_line.product_uom_qty
        response = self.zp_service.set_destination(
            zone_location.id, picking_type.id, move_line.id, dest_location.barcode, qty,
        )
        assert response["message"]["message_type"] == "success"
        self.assertEqual(move_line.state, "done")
        self.assertEqual(move_line.move_id.product_uom_qty, qty)

    def _location_content_transfer_process_line(self, move_line, set_destination=False):
        pack_location = move_line.location_id
        out_location = move_line.location_dest_id
        # Scan the location
        response = self.service.scan_location(pack_location.barcode)
        assert response["next_state"] in ("scan_destination_all", "start_single")
        # Set the destination
        if set_destination:
            qty = move_line.product_uom_qty
            if response["next_state"] == "scan_destination_all":
                response = self.service.set_destination_all(
                    pack_location.id, out_location.barcode
                )
                assert response["message"]["message_type"] == "success"
                self.assertEqual(move_line.state, "done")
                self.assertEqual(move_line.move_id.product_uom_qty, qty)
            elif response["next_state"] == "start_single":
                response = self.service.scan_line(
                    pack_location.id, move_line.id, move_line.product_id.barcode
                )
                assert response["message"]["message_type"] == "success"
                response = self.service.set_destination_line(
                    pack_location.id, move_line.id, qty, out_location.barcode
                )
                assert response["message"]["message_type"] == "success"
                assert move_line.state == "done"
                assert move_line.qty_done == qty

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
        pick_move_line1 = move_lines[0]
        pick_move_line2 = move_lines[1]
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
           to move the goods to PACK-1:

            move1 PICK -> PACK-1 'done'

        2) Operator-1 processes the second pallet with the "zone picking" scenario
           to move the goods to PACK-2:

            move1 PICK -> PACK-2 'done'

        3) Operator-2 with the "location content transfer" scenario scan
          the location where the first pallet is and has to found it:

            move1 PACK-1 -> SHIP
        """
        picking = self.picking1
        move_lines = picking.move_line_ids
        pick_move_line1 = move_lines[0]
        pick_move_line2 = move_lines[1]
        # Operator-1 process the first pallet with the "zone picking" scenario
        self._zone_picking_process_line(pick_move_line1)
        # Operator-1 process the second pallet with the "zone picking" scenario
        dest_location = pick_move_line2.location_dest_id.sudo().copy(
            {
                "name": pick_move_line2.location_dest_id.name + "_2",
                "barcode": pick_move_line2.location_dest_id.barcode + "_2",
                "location_id": pick_move_line2.location_dest_id.id,
            }
        )
        self._zone_picking_process_line(pick_move_line2, dest_location=dest_location)
        # Operator-3 with the "location content transfer" scenario scan
        # the location where the first pallet is
        pack_move_line2 = pick_move_line2.move_id.move_dest_ids.filtered(
            lambda m: m.state not in ("cancel", "done")
        ).move_line_ids.filtered(lambda l: not l.shopfloor_user_id)[0]
        self._location_content_transfer_process_line(pack_move_line2)
