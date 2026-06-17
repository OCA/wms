# Copyright 2026 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from .common import CommonCase


class TestFindWork(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menu.sudo().allow_get_work = True
        cls.location_src_a = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Source A",
                    "location_id": cls.location_src.id,
                }
            )
        )
        cls.location_src_b = (
            cls.env["stock.location"]
            .sudo()
            .create(
                {
                    "name": "Source B",
                    "location_id": cls.location_src.id,
                }
            )
        )
        cls.product = cls.product_a
        cls._add_stock_to_product(cls.product_a, cls.location_src_a, 10)
        cls._add_stock_to_product(cls.product_b, cls.location_src_b, 10)
        cls.picking_1 = cls._create_picking(lines=[(cls.product_a, 10)])
        cls.picking_2 = cls._create_picking(lines=[(cls.product_b, 10)])

    def test_find_work(self):
        response = self.service.dispatch("find_work")
        data = {"location": self._data_for_location(self.location_src_a)}
        self.assert_response(
            response,
            next_state="select_product",
            data=data,
        )

        # cancel select product to go back to find_work
        response = self.service.dispatch("scan_product__action_cancel")
        self.assert_response(
            response,
            next_state="get_work",
        )

        # cancel the first picking
        self.picking_1.action_cancel()
        response = self.service.dispatch("find_work")
        data = {"location": self._data_for_location(self.location_src_b)}
        self.assert_response(
            response,
            next_state="select_product",
            data=data,
        )
