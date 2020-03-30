from .common import CommonCase


class CheckoutCommonCase(CommonCase):
    @classmethod
    def setUpClass(cls, *args, **kwargs):
        super().setUpClass(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_checkout")
        cls.process = cls.menu.process_id
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.wh.delivery_steps = "pick_pack_ship"
        cls.picking_type = cls.process.picking_type_id

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="checkout")

    def _stock_picking_data(self, picking):
        return self.service._data_for_stock_picking(picking)

    # we test the methods that structure data in test_actions_data.py
    def _picking_summary_data(self, picking):
        return self.service.actions_for("data").picking_summary(picking)

    def _move_line_data(self, move_line):
        return self.service.actions_for("data").move_line(move_line)

    def _package_data(self, package, picking):
        return self.service.actions_for("data").package(package, picking=picking)

    def _packaging_data(self, packaging):
        return self.service.actions_for("data").packaging(packaging)
