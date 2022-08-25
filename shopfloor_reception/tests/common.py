# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.shopfloor.tests.common import CommonCase as BaseCommonCase


class CommonCase(BaseCommonCase):
    @classmethod
    def _create_picking(cls, picking_type=None, lines=None, confirm=True):
        picking = super()._create_picking(
            picking_type=picking_type, lines=lines, confirm=confirm
        )
        picking.user_id = False
        return picking

    def _data_for_move_lines(self, lines, **kw):
        return self.data.move_lines(lines, **kw)

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

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        cls.wh.sudo().reception_steps = "two_steps"

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
