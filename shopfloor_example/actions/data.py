# Copyright 2021 ACSONE SA/NV (http://www.acsone.eu)
# @author Simone Orsi <simahawk@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from odoo.addons.component.core import Component
from odoo.addons.shopfloor_base.utils import ensure_model


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @ensure_model("res.partner")
    def partner(self, record, **kw):
        return self._jsonify(record, self._partner_parser, **kw)

    def partners(self, records, **kw):
        return self.partner(records, multi=True)

    @property
    def _partner_detail_parser(self):
        return self._simple_record()
