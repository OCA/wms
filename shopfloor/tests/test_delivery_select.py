# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase


class DeliverySelectCase(DeliveryCommonCase):
    """Tests for /select"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls._fill_stock_for_moves(cls.picking1.move_lines)
        cls._fill_stock_for_moves(cls.picking2.move_lines)
        cls.pickings = cls.picking1 | cls.picking2
        cls.pickings.action_assign()

    def test_select_ok(self):
        response = self.service.dispatch(
            "select", params={"picking_id": self.picking1.id}
        )
        self.assert_response_deliver(response, picking=self.picking1)

    def test_select_not_found(self):
        response = self.service.dispatch("select", params={"picking_id": -1})
        self.assert_response_manual_selection(
            response,
            pickings=self.pickings,
            message=self.service.msg_store.stock_picking_not_found(),
        )
