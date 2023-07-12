# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .test_checkout_base import CheckoutCommonCase

# pylint: disable=missing-return


class CheckoutSummaryCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )

    def test_summary_picking_not_ready(self):
        response = self.service.dispatch(
            "summary", params={"picking_id": self.picking.id}
        )
        self.assert_response(
            response,
            next_state="select_document",
            data={"restrict_scan_first": False},
            message=self.service.msg_store.stock_picking_not_available(self.picking),
        )

    def test_summary_not_fully_processed(self):
        self._fill_stock_for_moves(self.picking.move_ids, in_package=True)
        self.picking.action_assign()
        # satisfy only few lines
        for ml in self.picking.move_line_ids[:2]:
            ml.qty_done = ml.reserved_uom_qty
            ml.shopfloor_checkout_done = True
        response = self.service.dispatch(
            "summary", params={"picking_id": self.picking.id}
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": False,
            },
        )

    def test_summary_fully_processed(self):
        self._fill_stock_for_moves(self.picking.move_ids, in_package=True)
        self.picking.action_assign()
        # satisfy only all lines
        for ml in self.picking.move_line_ids:
            ml.qty_done = ml.reserved_uom_qty
            ml.shopfloor_checkout_done = True
        response = self.service.dispatch(
            "summary", params={"picking_id": self.picking.id}
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": True,
            },
        )
