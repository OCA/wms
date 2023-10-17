# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.tests.common import Form

from .common import CommonCase


class SinglePackTransferCommonBase(CommonCase):
    @classmethod
    def setUpClassVars(cls, *args, **kwargs):
        super().setUpClassVars(*args, **kwargs)
        cls.menu = cls.env.ref("shopfloor.shopfloor_menu_demo_single_pallet_transfer")
        cls.profile = cls.env.ref("shopfloor_base.profile_demo_1")
        cls.picking_type = cls.menu.picking_type_ids
        cls.wh = cls.picking_type.warehouse_id

    @classmethod
    def setUpClassBaseData(cls, *args, **kwargs):
        super().setUpClassBaseData(*args, **kwargs)
        # we activate the move creation in tests when needed
        cls.menu.sudo().allow_move_create = False

        # disable the completion on the picking type, we'll have specific test(s)
        # to check the behavior of this screen
        cls.picking_type.sudo().display_completion_info = False

    def setUp(self):
        super().setUp()
        self.service = self.get_service(
            "single_pack_transfer", menu=self.menu, profile=self.profile
        )

    @classmethod
    def _create_initial_move(cls, lines):
        """Create the move to satisfy the pre-condition before /start"""
        picking_form = Form(cls.env["stock.picking"])
        picking_form.picking_type_id = cls.picking_type
        picking_form.location_id = cls.stock_location
        picking_form.location_dest_id = cls.shelf2
        for line in lines:
            with picking_form.move_ids_without_package.new() as move:
                move.product_id = line[0]
                move.product_uom_qty = line[1]
        picking = picking_form.save()
        picking.action_confirm()
        picking.action_assign()
        return picking
