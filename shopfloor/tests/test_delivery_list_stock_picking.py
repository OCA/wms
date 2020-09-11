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

    def test_list_stock_picking_ko(self):
        """No picking is ready, no picking to list."""
        response = self.service.dispatch("list_stock_picking", params={})
        self.assert_response_manual_selection(
            response, pickings=[],
        )

    def test_list_stock_picking_ok(self):
        """Picking ready to list."""
        # prepare 1st picking
        self._fill_stock_for_moves(self.picking1.move_lines)
        self.picking1.action_assign()
        response = self.service.dispatch("list_stock_picking", params={})
        # picking1 only available
        self.assert_response_manual_selection(
            response, pickings=self.picking1,
        )
        # prepare 2nd picking
        self._fill_stock_for_moves(self.picking2.move_lines)
        self.picking2.action_assign()
        response = self.service.dispatch("list_stock_picking", params={})
        # all pickings available
        self.assert_response_manual_selection(
            response, pickings=self.picking1 + self.picking2,
        )
