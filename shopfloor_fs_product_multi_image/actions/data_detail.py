# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from odoo.addons.component.core import Component

from .utils import _replace_image_fields


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    @property
    def _product_detail_parser(self):
        res = super(DataDetailAction, self)._product_detail_parser

        return _replace_image_fields(res, self._product_image_url)
