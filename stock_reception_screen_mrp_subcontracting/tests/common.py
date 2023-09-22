# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo import tests

from odoo.addons.stock_reception_screen.tests.common import Common


class MrpSubcontractingCommon(Common):
    @classmethod
    def _prepare_reception_screen(cls):
        # product.product_delivery_02 has a subcontracted BoM defined with
        # 'mrp_subcontracting' installed
        cls.picking = cls._create_picking_in(partner=cls.env.ref("base.res_partner_12"))
        cls._create_picking_line(cls.picking, cls.product_2, 4)
        cls.picking.action_confirm()
        cls.picking.action_reception_screen_open()
        cls.screen = cls.picking.reception_screen_id

    def _record_components_for_picking(self, picking):
        action = picking.action_record_components()
        if action:
            production = (
                self.env[action["res_model"]]
                .with_context(action["context"])
                .browse(action["res_id"])
            )
            wiz_form = tests.Form(production)
            wiz = wiz_form.save()
            wiz.qty_producing = wiz.product_qty
            wiz._onchange_producing()
            wiz.subcontracting_record_component()
