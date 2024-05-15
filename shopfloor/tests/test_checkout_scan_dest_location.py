# Copyright 2023 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

# pylint: disable=missing-return

from .test_checkout_base import CheckoutCommonCase


class CheckoutSelectChildLocationCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = picking = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls._fill_stock_for_moves(picking.move_ids)
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
        cls.child_location_view = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Child Location View",
                    "location_id": cls.dest_location.id,
                    "usage": "view",
                }
            )
        )

    def test_scan_dest_location_ok(self):
        response = self.service.dispatch(
            "scan_dest_location",
            params={
                "picking_id": self.picking.id,
                "barcode": self.child_location.name,
            },
        )

        self.assertRecordValues(self.picking, [{"state": "done"}])
        self.assertTrue(self.picking.backorder_ids)
        self.assertEqual(self.picking.backorder_ids.move_line_ids.reserved_uom_qty, 8)

        self.assert_response(
            response,
            next_state="select_document",
            data={"restrict_scan_first": False},
            message=self.service.msg_store.transfer_done_success(self.picking),
        )

    def test_scan_dest_location_not_found(self):
        response = self.service.dispatch(
            "scan_dest_location",
            params={
                "picking_id": self.picking.id,
                "barcode": "not-a-location",
            },
        )

        self.assert_response(
            response,
            next_state="select_child_location",
            data={
                "picking": self._stock_picking_data(
                    self.picking, done=True, with_lines=False, with_location=True
                ),
            },
            message=self.service.msg_store.location_not_found(),
        )

    def test_scan_dest_location_not_allowed(self):
        response = self.service.dispatch(
            "scan_dest_location",
            params={
                "picking_id": self.picking.id,
                "barcode": self.child_location_view.name,
            },
        )

        self.assert_response(
            response,
            next_state="select_child_location",
            data={
                "picking": self._stock_picking_data(
                    self.picking, done=True, with_lines=False, with_location=True
                ),
            },
            message=self.service.msg_store.dest_location_not_allowed(),
        )
