# Copyright 2020 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .test_delivery_base import DeliveryCommonCase


class DeliveryListStockPickingCase(DeliveryCommonCase):
    """Tests for /list_stock_picking"""

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking1 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )
        cls.picking2 = cls._create_picking(
            lines=[(cls.product_a, 10), (cls.product_b, 10)]
        )

    def assert_response_manual_selection(self, response, pickings=None, message=None):
        self.assert_response(
            response,
            next_state="manual_selection",
            data={
                "pickings": [self._stock_picking_data(picking) for picking in pickings]
            },
            message=message,
        )

    def test_list_stock_picking_ok(self):
        pickings = self.picking1 | self.picking2
        response = self.service.dispatch("list_stock_picking", params={})
        self.assert_response_manual_selection(
            response, pickings=pickings,
        )
