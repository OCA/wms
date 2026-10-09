# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.addons.component.core import Component


class DataDetailAction(Component):
    _inherit = "shopfloor.data.detail.action"

    @property
    def _product_detail_parser(self):
        res = super()._product_detail_parser
        return res + [
            (
                "product_tmpl_id:manufacturer",
                lambda rec, fname: self._jsonify(
                    rec.product_tmpl_id.manufacturer_id, ["id", "name"]
                ),
            ),
        ]
