# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase

# pylint: disable=missing-return


class PickingFormCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_checkout")
        cls.profile = cls.env.ref("shopfloor.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        cls.picking = cls._create_picking(lines=[(cls.product_a, 10)])

    def setUp(self):
        super().setUp()
        self.service = self.get_service("form_edit_stock_picking", profile=self.profile)

    def test_picking_form_get(self):
        available_carriers = self.service._get_available_carriers(self.picking)
        response = self.service.dispatch("get", self.picking.id)
        self.assert_response(
            response,
            data={
                "record": self.data_detail.picking_detail(self.picking),
                "form": {
                    "carrier_id": {
                        "value": self.picking.carrier_id.id,
                        "select_options": available_carriers.jsonify(["id", "name"]),
                    }
                },
            },
        )

    def test_picking_form_update(self):
        available_carriers = self.service._get_available_carriers(self.picking)
        self.picking.carrier_id = available_carriers[0]
        params = {"carrier_id": available_carriers[1].id}
        response = self.service.dispatch("update", self.picking.id, params=params)
        self.assert_response(
            response,
            data={
                "record": self.data_detail.picking_detail(self.picking),
                "form": {
                    "carrier_id": {
                        "value": self.picking.carrier_id.id,
                        "select_options": available_carriers.jsonify(["id", "name"]),
                    }
                },
            },
            message=self.service._msg_record_updated(self.picking),
        )
        self.assertRecordValues(
            self.picking, [{"carrier_id": available_carriers[1].id}]
        )
