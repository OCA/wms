# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from .common import CommonCase


class DeliveryCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_delivery")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"
        cls.product_e = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product E",
                    "type": "product",
                    "default_code": "E",
                    "barcode": "E",
                    "weight": 3,
                }
            )
        )
        cls.product_e_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_e.id,
                    "barcode": "ProductEBox",
                }
            )
        )
        cls.product_f = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product F",
                    "type": "product",
                    "default_code": "F",
                    "barcode": "F",
                    "weight": 3,
                }
            )
        )
        cls.product_f_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_f.id,
                    "barcode": "ProductFBox",
                }
            )
        )
        cls.product_g = (
            cls.env["product.product"]
            .sudo()
            .create(
                {
                    "name": "Product G",
                    "type": "product",
                    "default_code": "G",
                    "barcode": "G",
                    "weight": 1,
                }
            )
        )
        cls.product_g_packaging = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "name": "Box",
                    "product_id": cls.product_g.id,
                    "barcode": "ProductGBox",
                }
            )
        )

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "delivery", menu=self.menu, profile=self.profile
        )

    def _stock_picking_data(self, picking):
        return self.service.data_detail.picking_detail(picking)

    def _stock_location_data(self, location):
        return self.service.data.location(location)

    def assert_response_deliver(
        self, response, picking=None, message=None, location=None
    ):
        self.assert_response(
            response,
            next_state="deliver",
            data={
                "picking": self._stock_picking_data(picking) if picking else None,
                "sublocation": self._stock_location_data(location)
                if location
                else None,
            },
            message=message,
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

    def assert_qty_done(self, move_lines, qties=None):
        """Ensure that the quantities done are the expected ones.

        If `qties` is not defined, the expected qties are `product_uom_qty`
        of the move lines.
        `qties` parameter is a list of move lines qty (same order).
        """
        if qties:
            assert len(move_lines) == len(qties), "'qties' doesn't match 'move_lines'"
            expected_qties = []
            for qty in qties:
                expected_qties.append({"qty_done": qty})
        else:
            expected_qties = [{"qty_done": line.product_uom_qty} for line in move_lines]
        self.assertRecordValues(move_lines, expected_qties)
        package_level = move_lines.package_level_id
        if package_level:
            values = [{"is_done": True}]
            if qties:
                values = [{"is_done": bool(qty)} for qty in qties]
            # we have a package level only when there is a package
            self.assertRecordValues(package_level, values)
