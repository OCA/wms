# Copyright 2021 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)


from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _move_line_parser(self):
        res = super()._move_line_parser
        res.append("has_lq_products")
        return res

    @property
    def _package_parser(self):
        res = super()._package_parser
        res.append("has_lq_products")
        return res
