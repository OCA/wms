# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo import fields

from odoo.addons.shopfloor.tests.common import CommonCase as BaseCommonCase


class CommonCase(BaseCommonCase):
    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True, **kw):
        picking = super()._create_picking(
            picking_type=picking_type, lines=lines, confirm=confirm, **kw
        )
        picking.user_id = False
        return picking

    @classmethod
    def _create_lot(cls, **kwargs):
        vals = {
            "product_id": cls.product_a.id,
            "company_id": cls.env.company.id,
        }
        vals.update(kwargs)
        return cls.env["stock.production.lot"].create(vals)

    @classmethod
    def _add_package(cls, picking):
        packaging_ids = [
            cls.product_a_packaging.id,
            cls.product_c_packaging.id,
            cls.product_b_packaging.id,
            cls.product_d_packaging.id,
        ]
        packagings = cls.env["product.packaging"].browse(packaging_ids)
        for line in picking.move_line_ids:
            product = line.product_id
            packaging = packagings.filtered(lambda p: p.product_id == product)
            package = cls.env["stock.quant.package"].create(
                {"product_packaging_id": packaging.id}
            )
            line.package_id = package

    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor_reception.shopfloor_menu_demo_reception")
        cls.profile = cls.env.ref("shopfloor.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

    def _data_for_picking_with_line(self, picking):
        picking_data = self._data_for_picking(picking)
        move_lines_data = self._data_for_move_lines(picking.move_line_ids)
        picking_data.update({"move_lines": move_lines_data})
        return picking_data

    def _data_for_pickings_with_line(self, pickings):
        res = []
        for picking in pickings:
            res.append(self._data_for_picking_with_line(picking))
        return res

    def _data_for_picking_with_moves(self, picking, with_progress=True):
        picking_data = self._data_for_picking(picking, with_progress)
        moves_data = self._data_for_moves(picking.move_lines)
        picking_data.update({"moves": moves_data})
        return picking_data

    def _data_for_picking(self, picking, with_progress=True):
        return self.data.picking(picking, with_progress=with_progress)

    def _data_for_pickings(self, pickings):
        res = []
        for picking in pickings:
            res.append(self._data_for_picking(picking))
        return res

    def _data_for_move(self, move):
        return self.data.move(move)

    def _data_for_moves(self, moves):
        res = []
        for move in moves:
            res.append(self._data_for_move(move))
        return res

    def _data_for_select_move(self, picking, with_progress=True):
        picking_data = self._data_for_picking_with_moves(picking, with_progress)
        data = {
            "picking": picking_data,
        }
        return data

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "reception", menu=self.menu, profile=self.profile
        )

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

    def _get_all_pickings(self):
        return self.env["stock.picking"].search(
            [
                ("state", "=", "assigned"),
                ("picking_type_id", "=", self.picking_type.id),
                ("user_id", "=", False),
            ],
            order="scheduled_date ASC",
        )

    def _get_today_pickings(self):
        return self.env["stock.picking"].search(
            [
                ("state", "=", "assigned"),
                ("picking_type_id", "=", self.picking_type.id),
                ("user_id", "=", False),
                ("scheduled_date", "=", fields.Datetime.today()),
            ],
            order="scheduled_date ASC",
        )

    def assertMessage(self, response, expected_message):
        message = response.get("message")
        for key, value in expected_message.items():
            self.assertEqual(message.get(key), value)

    @classmethod
    def _get_move_ids_from_response(cls, response):
        state = response.get("next_state")
        data = response["data"][state]
        picking_data = data.get("pickings") or [data.get("picking")]
        moves_data = []
        for picking in picking_data:
            moves_data.extend(picking["moves"])
        return [move["id"] for move in moves_data]

    def _get_service_for_user(self, user):
        user_env = self.env(user=user)
        return self.get_service(
            "reception", menu=self.menu, profile=self.profile, env=user_env
        )

    @classmethod
    def _shopfloor_manager_values(cls):
        vals = super()._shopfloor_manager_values()
        vals["groups_id"] = [(6, 0, [cls.env.ref("stock.group_stock_user").id])]
        return vals
