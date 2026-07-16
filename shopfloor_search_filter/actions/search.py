# Copyright 2026 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


from odoo.addons.component.core import Component


class SearchAction(Component):
    _inherit = "shopfloor.search.action"

    def find(self, barcode: str, types: list[str] = None):
        search_result = super().find(barcode, types)
        menu = getattr(self.work, "menu", None)
        if not menu:
            return search_result

        type_to_menu_option = {
            "product": menu.allow_product_scan,
            "package": menu.allow_package_scan,
            "picking": menu.allow_picking_scan,
            "location": menu.allow_location_scan,
            "lot": menu.allow_lot_scan,
            "packaging": menu.allow_packaging_scan,
        }
        allowed_types = [
            _type for _type, menu_option in type_to_menu_option.items() if menu_option
        ]
        if search_result.type not in allowed_types:
            return self._make_search_result(
                type="none", parse_result=search_result.parse_result
            )
        return search_result
