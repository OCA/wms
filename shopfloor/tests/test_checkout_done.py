from .test_checkout_base import CheckoutCommonCase


class CheckoutDoneCase(CheckoutCommonCase):
    def test_done_ok(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        # line is done
        picking.move_line_ids.write({"qty_done": 10, "shopfloor_checkout_packed": True})
        response = self.service.dispatch("done", params={"picking_id": picking.id})

        self.assertRecordValues(picking, [{"state": "done"}])

        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "success",
                "message": "Transfer {} done".format(picking.name),
            },
        )


class CheckoutDonePartialCase(CheckoutCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        cls.line1 = picking.move_line_ids[0]
        cls.line2 = picking.move_line_ids[1]
        cls.line1.write({"qty_done": 10, "shopfloor_checkout_packed": True})
        cls.line2.write({"qty_done": 2, "shopfloor_checkout_packed": True})

    def test_done_partial(self):
        # line is done
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})

        self.assertRecordValues(self.picking, [{"state": "assigned"}])

        self.assert_response(
            response,
            next_state="confirm_done",
            data={"picking": self._stock_picking_data(self.picking)},
            message={
                "message_type": "warning",
                "message": "Not all lines have been processed, do"
                " you want to confirm partial operation?",
            },
        )

    def test_done_partial_confirm(self):
        # line is done
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirmation": True}
        )

        self.assertRecordValues(self.picking, [{"state": "done"}])
        self.assertTrue(self.picking.backorder_ids)

        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "success",
                "message": "Transfer {} done".format(self.picking.name),
            },
        )


class CheckoutDoneRawUnpackedCase(CheckoutCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        cls.line1 = picking.move_line_ids[0]
        cls.line2 = picking.move_line_ids[1]
        cls.package = cls.env["stock.quant.package"].create({})
        cls.line1.write(
            {
                "qty_done": 10,
                "shopfloor_checkout_packed": True,
                "result_package_id": cls.package.id,
            }
        )
        cls.line2.write({"qty_done": 10, "shopfloor_checkout_packed": False})

    def test_done_partial(self):
        # line is done
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})

        self.assertRecordValues(self.picking, [{"state": "assigned"}])

        self.assert_response(
            response,
            next_state="confirm_done",
            data={"picking": self._stock_picking_data(self.picking)},
            message={
                "message_type": "warning",
                "message": "Remaining raw product not packed, proceed anyway?",
            },
        )

    def test_done_partial_confirm(self):
        # line is done
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirmation": True}
        )

        self.assertRecordValues(self.picking, [{"state": "done", "backorder_ids": []}])
        self.assertRecordValues(
            self.line1 + self.line2,
            [{"result_package_id": self.package.id}, {"result_package_id": False}],
        )

        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "success",
                "message": "Transfer {} done".format(self.picking.name),
            },
        )
