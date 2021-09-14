# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
import os

from odoo.addons.shopfloor.services.checkout import Checkout


class CheckoutExt(Checkout):
    _inherit = "base.shopfloor.process"

    def _data_for_packing_info(self, picking):
        res = super()._data_for_packing_info(picking)
        if picking.picking_type_id.shopfloor_display_packing_info:
            shopfloor_packing_info = (
                picking.shopfloor_packing_info_id.text
                if picking.shopfloor_packing_info_id
                else ""
            )
            if shopfloor_packing_info:
                res += "{}{}".format(os.linesep, shopfloor_packing_info).strip()
        return res
