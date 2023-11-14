# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase


class CheckoutDoneCase(CheckoutCommonCase):
    def test_done_ok(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        # line is done
        picking.move_line_ids.write({"qty_done": 10, "shopfloor_checkout_done": True})
        response = self.service.dispatch("done", params={"picking_id": picking.id})

        self.assertRecordValues(picking, [{"state": "done"}])

        self.assert_response(
            response,
            next_state="select_document",
            message={
                "message_type": "success",
                "body": "Transfer {} done".format(picking.name),
            },
            data={"restrict_scan_first": False},
        )


class CheckoutDonePartialCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        cls.line1 = picking.move_line_ids[0]
        cls.line2 = picking.move_line_ids[1]
        cls.line1.write({"qty_done": 10, "shopfloor_checkout_done": True})
        cls.line2.write({"qty_done": 2, "shopfloor_checkout_done": True})

        cls.dest_location = picking.location_dest_id
        cls.child_location = (
            cls.env["stock.location"]
            .sudo()
            .create({"name": "Child Location", "location_id": cls.dest_location.id})
        )

    def test_done_partial(self):
        # line is done
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})

        self.assertRecordValues(self.picking, [{"state": "assigned"}])

        self.assert_response(
            response,
            next_state="confirm_done",
            data={"picking": self._stock_picking_data(self.picking, done=True)},
            message=self.service.msg_store.transfer_confirm_done(),
        )

    def test_done_partial_confirm(self):
        # lines are done
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirmation": True}
        )

        self.assertRecordValues(self.picking, [{"state": "done"}])

        self.assert_response(
            response,
            next_state="select_document",
            message=self.service.msg_store.transfer_done_success(self.picking),
            data={"restrict_scan_first": False},
        )

    def test_done_ask_destination_location(self):
        """Check asking for destination location for view type location."""
        view_location = (
            self.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Test Location Usage View",
                    "location_id": self.picking.move_lines.location_dest_id.id,
                    "usage": "view",
                }
            )
        )
        self.picking.move_lines.location_dest_id = view_location
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirmation": True}
        )

        self.assertRecordValues(self.picking, [{"state": "assigned"}])
        self.assert_response(
            response,
            next_state="select_child_location",
            data={
                "picking": self._stock_picking_data(
                    self.picking, done=True, with_lines=False, with_location=True
                ),
            },
        )


class CheckoutDoneRawUnpackedCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
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
                "shopfloor_checkout_done": True,
                "result_package_id": cls.package.id,
            }
        )
        cls.line2.write({"qty_done": 10, "shopfloor_checkout_done": False})

    def test_done_partial(self):
        # line is done
        response = self.service.dispatch("done", params={"picking_id": self.picking.id})

        self.assertRecordValues(self.picking, [{"state": "assigned"}])

        self.assert_response(
            response,
            next_state="confirm_done",
            data={"picking": self._stock_picking_data(self.picking, done=True)},
            message={
                "message_type": "warning",
                "body": "Remaining raw product not packed, proceed anyway?",
            },
        )

    def test_done_partial_confirm(self):
        # line is done
        response = self.service.dispatch(
            "done", params={"picking_id": self.picking.id, "confirmation": True}
        )

        # it has been extracted in its own picking, the current one staying open
        picking_done = self.line1.picking_id
        self.assertRecordValues(picking_done, [{"state": "done", "backorder_ids": []}])
        self.assertRecordValues(
            self.picking, [{"state": "assigned", "backorder_ids": [picking_done.id]}]
        )
        self.assertRecordValues(
            self.line1 + self.line2,
            [{"result_package_id": self.package.id}, {"result_package_id": False}],
        )
        self.assertIn(self.line2, self.picking.move_line_ids)

        self.assert_response(
            response,
            next_state="select_document",
            message=self.service.msg_store.transfer_done_success(picking_done),
            data={"restrict_scan_first": False},
        )
