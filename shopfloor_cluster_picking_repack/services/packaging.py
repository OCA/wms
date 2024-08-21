# Copyright 2020-2021 Camptocamp SA (http://www.camptocamp.com)
# Copyright 2020-2021 Jacques-Etienne Baudoux (BCIM) <je@bcim.be>
# Copyright 2024 ACSONE SA/NV (https://www.acsone.eu)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).


from odoo.addons.component.core import Component
from odoo.addons.stock.models.stock_picking import Picking


class PackagingAction(Component):

    _inherit = "shopfloor.packaging.action"

    def _check_put_in_pack(
        self,
        record,
        picking: Picking,
        response_error_func: callable,
        nbr_packages: int = None,
        package_type_id: int = None,
    ):
        """
        This will check if parameters are correct and return a response with
        the appropriate message.
        """
        if not picking:
            return response_error_func(
                record,
                message=self.msg_store.stock_picking_not_found(),
            )
        if not picking.is_shopfloor_packing_todo:
            return response_error_func(
                record,
                message=self.msg_store.stock_picking_already_packed(picking),
            )
        if isinstance(nbr_packages, int) and nbr_packages <= 0:
            return response_error_func(
                record,
                message=self.msg_store.nbr_packages_must_be_greated_than_zero(),
            )
        # Check if package type exists
        if package_type_id and not nbr_packages:
            package_type = (
                self.env["stock.package.type"].browse(package_type_id).exists()
            )
            if not package_type:
                return response_error_func(
                    record,
                    message=self.msg_store.record_not_found(),
                )
        return False

    def _scan_package_find(self, picking, barcode, search_types=None):
        search = self._actions_for("search")
        search_types = (
            "package",
            "product",
            "packaging",
            "lot",
            "serial",
            "delivery_packaging",
        )
        return search.find(
            barcode,
            types=search_types,
            handler_kw=dict(
                lot=dict(products=picking.move_ids.product_id),
                serial=dict(products=picking.move_ids.product_id),
            ),
        )

    def _check_scan_package_find(self, picking, search_result):
        # Used by inheriting modules
        return False
