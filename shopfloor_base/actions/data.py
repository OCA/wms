# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl.html).
from odoo.addons.component.core import Component

from ..utils import ensure_model


class DataAction(Component):
    """Provide methods to share data structures

    The methods should be used in Service Components, so we try to
    have similar data structures across scenarios.
    """

    _name = "shopfloor.data.action"
    _inherit = "shopfloor.process.action"
    _usage = "data"

    def _jsonify(self, recordset, parser, multi=False, **kw):
        res = recordset.jsonify(parser)
        if not multi:
            return res[0] if res else None
        return res

    def _simple_record_parser(self):
        return ["id", "name"]

    def _select_value_to_label(self, rec, fname):
        return rec._fields[fname].convert_to_export(rec[fname], rec)

    @ensure_model("res.partner")
    def partner(self, record, **kw):
        return self._jsonify(record, self._partner_parser, **kw)

    def partners(self, record, **kw):
        return self.partner(record, multi=True)

    @property
    def _partner_parser(self):
        return ["id", "display_name:name"]
