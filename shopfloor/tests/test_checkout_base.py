# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase


class CheckoutCommonCase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_checkout")
        cls.profile = cls.env.ref("shopfloor.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().delivery_steps = "pick_pack_ship"

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "checkout", menu=self.menu, profile=self.profile
        )

    def _stock_picking_data(
        self, picking, done=False, with_lines=True, with_location=False, **kw
    ):
        return self.service._data_for_stock_picking(
            picking, done, with_lines, with_location, **kw
        )

    def _stock_locations_data(self, locations, **kw):
        return self.service._data_for_locations(locations, **kw)

    # we test the methods that structure data in test_actions_data.py
    def _picking_summary_data(self, picking):
        return self.data.picking(picking)

    def _move_line_data(self, move_line):
        return self.data.move_line(move_line)

    def _package_data(self, package, picking, **kwargs):
        return self.data.package(
            package, picking=picking, with_packaging=True, **kwargs
        )

    def _packaging_data(self, packaging):
        return self.data.packaging(packaging)

    def _data_for_select_line(self, picking, **kw):
        data = {
            "picking": self._stock_picking_data(picking),
            "group_lines_by_location": True,
            "show_oneline_package_content": False,
            "need_confirm_pack_all": False,
            "need_confirm_lot": None,
        }
        data.update(kw)
        return data

    def _assert_select_package_qty_above(self, response, picking):
        self.assert_response(
            response,
            next_state="select_package",
            data={
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in picking.move_line_ids.sorted()
                ],
                "picking": self._picking_summary_data(picking),
                "no_package_enabled": True,
            },
            message={
                "message_type": "warning",
                "body": "The quantity scanned for one or more lines cannot be "
                "higher than the maximum allowed.",
            },
        )
