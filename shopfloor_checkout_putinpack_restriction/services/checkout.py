# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)


from odoo.addons.component.core import Component


class Checkout(Component):
    _inherit = "shopfloor.checkout"

    def _data_response_for_select_package(self, picking, lines, message=None):
        res = super()._data_response_for_select_package(picking, lines)
        if picking.put_in_pack_restriction == "no_package":
            res["package_allowed"] = False
        elif picking.put_in_pack_restriction == "with_package":
            res["no_package_enabled"] = False
        return res

    def _check_scan_package_find(self, picking, search_result):
        if search_result.type in ["package", "delivery_packaging"]:
            if picking.put_in_pack_restriction == "no_package":
                return self.msg_store.package_not_allowed_for_operation()
        return super()._check_scan_package_find(picking, search_result)
