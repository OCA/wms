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

    def _scan_package_action_from_package(
        self, picking, selected_lines, record, **kwargs
    ):
        if picking.put_in_pack_restriction == "no_package":
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.package_not_allowed_for_operation(),
            )
        return super()._scan_package_action_from_package(
            picking, selected_lines, record, **kwargs
        )

    def _scan_package_action_from_delivery_packaging(
        self, picking, selected_lines, record, **kwargs
    ):
        if picking.put_in_pack_restriction == "no_package":
            return self._response_for_select_package(
                picking,
                selected_lines,
                message=self.msg_store.package_not_allowed_for_operation(),
            )
        return super()._scan_package_action_from_delivery_packaging(
            picking, selected_lines, record, **kwargs
        )
