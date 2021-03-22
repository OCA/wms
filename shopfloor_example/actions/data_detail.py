# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    @ensure_model("res.partner")
    def partner_detail(self, record, **kw):
        return self._jsonify(record, self._partner_detail_parser, **kw)

    def partner_details(self, record, **kw):
        return self.partner_detail(record, multi=True)

    @property
    def _partner_detail_parser(self):
        return ["id", "name", "ref", "email"]
