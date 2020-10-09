# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase


class CheckoutListStockPickingCase(CheckoutCommonCase):
    def test_list_stock_picking(self):
        picking1 = self._create_picking()
        picking2 = self._create_picking()
        # should not be in the list because another type:
        picking3 = self._create_picking(picking_type=self.wh.pick_type_id)
        # should not be in list because not assigned:
        self._create_picking()
        to_assign = picking1 | picking2 | picking3
        self._fill_stock_for_moves(to_assign.move_lines, in_package=True)
        to_assign.action_assign()
        response = self.service.dispatch("list_stock_picking", params={})
        expected = {
            "pickings": [
                self._picking_summary_data(picking1),
                self._picking_summary_data(picking2),
            ]
        }

        self.assert_response(response, next_state="manual_selection", data=expected)


class CheckoutSelectCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking()
        cls._fill_stock_for_moves(cls.picking.move_lines, in_package=True)
        cls.picking.action_assign()

    def test_select_ok(self):
        response = self.service.dispatch(
            "select", params={"picking_id": self.picking.id}
        )
        self.assert_response(
            response,
            next_state="select_line",
            data={"picking": self._stock_picking_data(self.picking)},
        )

    def _test_error(self, picking, msg):
        response = self.service.dispatch("select", params={"picking_id": picking.id})
        self.assert_response(
            response,
            next_state="manual_selection",
            message={"message_type": "error", "body": msg},
            data={"pickings": [self._picking_summary_data(self.picking)]},
        )

    def test_select_error_not_found(self):
        picking = self._create_picking()
        picking.sudo().unlink()
        self._test_error(
            picking, self.service.msg_store.stock_picking_not_found()["body"]
        )

    def test_select_error_not_available(self):
        picking = self._create_picking()
        self._test_error(
            picking, self.service.msg_store.stock_picking_not_available(picking)["body"]
        )

    def test_select_error_not_allowed(self):
        picking = self._create_picking(picking_type=self.wh.pick_type_id)
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        self._test_error(
            picking, "You cannot move this using this menu.".format(picking.name)
        )
