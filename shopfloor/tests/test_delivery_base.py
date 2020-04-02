from .common import CommonCase


class DeliveryCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_delivery")
        cls.profile = cls.env.ref("shopfloor.shopfloor_profile_shelf_1_demo")
        cls.wh = cls.profile.warehouse_id
        cls.picking_type = cls.menu.picking_type_ids

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"

    def setUp(self):
        super().setUp()
        with self.work_on_services(menu=self.menu, profile=self.profile) as work:
            self.service = work.component(usage="delivery")

    def _stock_picking_data(self, picking):
        return self.service._data_for_stock_picking(picking)

    def assert_response_deliver(self, response, picking=None, message=None):
        self.assert_response(
            response,
            next_state="deliver",
            data={"picking": self._stock_picking_data(picking) if picking else None},
            message=message,
        )
