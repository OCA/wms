# Copyright 2022 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestStart(CommonCase):
    def test_start(self):
        response = self.service.dispatch("start")
        self.assert_response(response, next_state="select_location_or_package", data={})

    def test_start_with_work(self):
        self.menu.sudo().allow_get_work = True
        response = self.service.dispatch("start")

        self.assert_response(response, next_state="get_work")

    def _check_recover(self):
        product = self.product_a
        location = self.location_src
        self._add_stock_to_product(product, location, 10)
        picking = self._create_picking(lines=[(product, 10)])

        picking.user_id = self.env.user
        move_line = picking.move_line_ids
        move_line.qty_done = move_line.reserved_uom_qty
        response = self.service.dispatch("start")
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": None,
        }
        message = {
            "message_type": "info",
            "body": "Recovered previous session.",
        }
        self.assert_response(
            response, next_state="set_quantity", data=data, message=message
        )

    def test_recover(self):
        self._check_recover()

    def test_recover_with_work(self):
        self.menu.sudo().allow_get_work = True
        self._check_recover()
