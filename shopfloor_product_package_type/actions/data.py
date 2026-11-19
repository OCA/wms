# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _product_parser(self):
        res = super()._product_parser
        res += [
            (
                "package_type_id:package_type",
                self._simple_record_parser() + ["display_name"],
            )
        ]
        return res
