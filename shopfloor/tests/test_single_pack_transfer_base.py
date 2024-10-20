# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020 Akretion (http://www.akretion.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .common import CommonCase

# pylint: disable=missing-return


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
