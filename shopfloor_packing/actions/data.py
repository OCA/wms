# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo.addons.component.core import Component


class DataAction(Component):
    _inherit = "shopfloor.data.action"

    @property
    def _package_parser(self):
        res = super()._package_parser
        res.append("is_internal")
        return res

    def _data_for_packing_info(self, picking):
        """Return the packing information

        Intended to be extended.
        """
        # TODO: This could be avoided if included in the picking parser.
        return ""

    def select_package(self, picking, lines):
        return {
            "selected_move_lines": self.move_lines(lines.sorted()),
            "picking": self.picking(picking),
            "packing_info": self._data_for_packing_info(picking),
            # "no_package_enabled": not self.options.get("checkout__disable_no_package"),
            # Used by inheriting module
            "package_allowed": True,
        }
