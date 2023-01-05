# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_cluster_picking_base import ClusterPickingCommonCase


class ClusterPickingScanDestinationPackCase(ClusterPickingCommonCase):
    """Tests covering the /scan_destination_pack endpoint

    After a batch has been selected and the user confirmed they are
    working on it, user picked the good, now they scan the location
    destination.
    """

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.batch = cls._create_picking_batch(
            [
                [
                    cls.BatchProduct(product=cls.product_a, quantity=10),
                    cls.BatchProduct(product=cls.product_b, quantity=10),
                ],
                [cls.BatchProduct(product=cls.product_a, quantity=10)],
            ]
        )
        cls.one_line_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 1
        )
        cls.two_lines_picking = cls.batch.picking_ids.filtered(
            lambda picking: len(picking.move_lines) == 2
        )

        cls.bin1 = cls.env["stock.quant.package"].create({})
        cls.bin2 = cls.env["stock.quant.package"].create({})

        cls._simulate_batch_selected(cls.batch)

    def test_scan_destination_pack_ok(self):
        """Happy path for scan destination package

        It sets the line in the pack for the full qty
        """
        line = self.batch.picking_ids.move_line_ids[0]
        next_line = self.batch.picking_ids.move_line_ids[1]
        qty_done = line.product_uom_qty
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": qty_done,
            },
        )
        self.assertRecordValues(
            line, [{"qty_done": qty_done, "result_package_id": self.bin1.id}]
        )
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )

    def test_scan_destination_pack_ok_last_line(self):
        """Happy path for scan destination package

        It sets the line in the pack for the full qty
        """
        self._set_dest_package_and_done(self.one_line_picking.move_line_ids, self.bin1)
        self._set_dest_package_and_done(
            self.two_lines_picking.move_line_ids[0], self.bin2
        )
        # this is the only remaining line to pick
        line = self.two_lines_picking.move_line_ids[1]
        qty_done = line.product_uom_qty
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin2.name,
                "quantity": qty_done,
            },
        )
        self.assertRecordValues(
            line, [{"qty_done": qty_done, "result_package_id": self.bin2.id}]
        )
        data = self._data_for_batch(self.batch, self.packing_location)
        self.assert_response(
            response,
            # they reach the same destination so next state unload_all
            next_state="unload_all",
            data=data,
        )

    def test_scan_destination_pack_not_empty_same_picking(self):
        """Scan a destination package with move lines of same picking"""
        line1 = self.two_lines_picking.move_line_ids[0]
        line2 = self.two_lines_picking.move_line_ids[1]
        # we already scan and put the first line in bin1
        self._set_dest_package_and_done(line1, self.bin1)
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line2.id,
                # this bin is used for the same picking, should be allowed
                "barcode": self.bin1.name,
                "quantity": line2.product_uom_qty,
            },
        )
        self.assert_response(
            response,
            next_state="start_line",
            # we did not pick this line, so it should go there
            data=self._line_data(self.one_line_picking.move_line_ids),
            message=self.ANY,
        )

    def test_scan_destination_pack_not_empty_different_picking(self):
        """Scan a destination package with move lines of other picking"""
        # do as if the user already picked the first good (for another picking)
        # and put it in bin1
        self._set_dest_package_and_done(self.one_line_picking.move_line_ids, self.bin1)
        line = self.two_lines_picking.move_line_ids[0]
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                # this bin is used for the other picking
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )
        self.assertRecordValues(line, [{"qty_done": 0, "result_package_id": False}])
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line),
            message={
                "message_type": "error",
                "body": "The destination bin {} is not empty,"
                " please take another.".format(self.bin1.name),
            },
        )

    def test_scan_destination_pack_not_empty_multi_pick_allowed(self):
        """Scan a destination package with move lines of other picking"""
        # do as if the user already picked the first good (for another picking)
        # and put it in bin1
        self.menu.sudo().write(
            {"unload_package_at_destination": True, "multiple_move_single_pack": True}
        )
        self._set_dest_package_and_done(self.one_line_picking.move_line_ids, self.bin1)
        line = self.two_lines_picking.move_line_ids[0]
        self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                # this bin is used for the other picking
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )
        # Since `multiple_move_single_pack` is enabled, assigning `bin` should be ok
        new_line = self.two_lines_picking.move_line_ids - line
        self.assertRecordValues(
            line,
            [
                {
                    "qty_done": 10,
                    "result_package_id": self.bin1.id,
                    "product_uom_qty": 10,
                }
            ],
        )
        self.assertRecordValues(
            new_line,
            [{"qty_done": 0, "result_package_id": False, "product_uom_qty": 10}],
        )

    def test_scan_destination_pack_bin_not_found(self):
        """Scan a destination package that do not exist"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                # this bin is used for the other picking
                "barcode": "⌿",
                "quantity": line.product_uom_qty,
            },
        )
        line_data = self._line_data(line)
        line_data["qty_done"] = 10
        self.assert_response(
            response,
            next_state="scan_destination",
            data=line_data,
            message={
                "message_type": "error",
                "body": "Bin {} doesn't exist".format("⌿"),
            },
        )

    def test_scan_destination_pack_quantity_more(self):
        """Pick more units than expected"""
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty + 1,
            },
        )
        self.assert_response(
            response,
            next_state="scan_destination",
            data=self._line_data(line),
            message={
                "message_type": "error",
                "body": "You must not pick more than {} units.".format(
                    line.product_uom_qty
                ),
            },
        )

    def test_scan_destination_pack_quantity_less(self):
        """Pick less units than expected"""
        line = self.one_line_picking.move_line_ids
        quant = self.env["stock.quant"].search(
            [
                ("location_id", "=", line.location_id.id),
                ("product_id", "=", line.product_id.id),
            ]
        )
        quant.ensure_one()
        self.assertRecordValues(quant, [{"quantity": 40.0, "reserved_quantity": 20.0}])

        # when we pick less quantity than expected, the line is split
        # and the user is proposed to pick the next line for the remaining
        # quantity
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty - 3,
            },
        )
        new_line = self.one_line_picking.move_line_ids - line

        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(new_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )

        self.assertRecordValues(
            line,
            [{"qty_done": 7, "result_package_id": self.bin1.id, "product_uom_qty": 7}],
        )
        self.assertRecordValues(
            new_line,
            [{"qty_done": 0, "result_package_id": False, "product_uom_qty": 3}],
        )
        # the reserved quantity on the quant must stay the same
        self.assertRecordValues(quant, [{"quantity": 40.0, "reserved_quantity": 20.0}])

    def test_scan_destination_pack_zero_check_activated(self):
        """Location will be emptied, have to go to zero check"""
        # ensure that the location used for the test will contain only what we want
        self.zero_check_location = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "ZeroCheck",
                    "location_id": self.stock_location.id,
                    "barcode": "ZEROCHECK",
                }
            )
        )
        line = self.one_line_picking.move_line_ids
        location, product, qty = (
            self.zero_check_location,
            line.product_id,
            line.product_uom_qty,
        )
        self.one_line_picking.do_unreserve()

        # ensure we have activated the zero check
        self.one_line_picking.picking_type_id.sudo().shopfloor_zero_check = True
        # Update the quantity in the location to be equal to the line's
        # so when scan_destination_pack sets the qty_done, the planned
        # qty should be zero and trigger a zero check
        self._update_qty_in_location(location, product, qty)
        # Reserve goods (now the move line has the expected source location)
        self.one_line_picking.move_lines.location_id = location
        self.one_line_picking.action_assign()
        line = self.one_line_picking.move_line_ids
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )

        self.assert_response(
            response,
            next_state="zero_check",
            data={
                "id": line.id,
                "location_src": self.data.location(line.location_id),
                "batch": self.data.picking_batch(self.batch),
            },
        )

    def test_scan_destination_pack_zero_check_disabled(self):
        """Location will be emptied, no zero check, continue"""
        line = self.one_line_picking.move_line_ids
        # ensure we have deactivated the zero check
        self.one_line_picking.picking_type_id.sudo().shopfloor_zero_check = False
        # Update the quantity in the location to be equal to the line's
        # so when scan_destination_pack sets the qty_done, the planned
        # qty should be zero and trigger a zero check
        self._update_qty_in_location(
            line.location_id, line.product_id, line.product_uom_qty
        )
        response = self.service.dispatch(
            "scan_destination_pack",
            params={
                "picking_batch_id": self.batch.id,
                "move_line_id": line.id,
                "barcode": self.bin1.name,
                "quantity": line.product_uom_qty,
            },
        )

        next_line = self.two_lines_picking.move_line_ids[0]
        # continue to the next one, no zero check
        self.assert_response(
            response,
            next_state="start_line",
            data=self._line_data(next_line),
            message={
                "message_type": "success",
                "body": "{} {} put in {}".format(
                    line.qty_done, line.product_id.display_name, self.bin1.name
                ),
            },
        )
