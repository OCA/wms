# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase


class CheckoutCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_checkout")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="checkout")

    def _stock_picking_data(self, picking, **kw):
        return self.service._data_for_stock_picking(picking, **kw)

    # we test the methods that structure data in test_actions_data.py
    def _picking_summary_data(self, picking):
        return self.data.picking(picking)

    def _move_line_data(self, move_line):
        return self.data.move_line(move_line)

    def _package_data(self, package, picking):
        return self.data.package(package, picking=picking, with_packaging=True)

    def _packaging_data(self, packaging):
        return self.data.packaging(packaging)
