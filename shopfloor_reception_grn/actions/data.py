# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _picking_parser(self):
        res = super()._picking_parser
        res += [("grn_id:grn", self._grn_parser)]
        return res

    @property
    def _grn_parser(self):
        return self._simple_record_parser()
