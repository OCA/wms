# Copyright 2021 Camptocamp SA (https://www.camptocamp.com)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html)
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutScanLineCaseBase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def _test_scan_line_ok(
        self, barcode, selected_lines, related_lines=None, packing_info=""
    ):
        """Test /scan_line with a valid return

        :param barcode: the barcode we scan
        :selected_lines: expected move lines returned by the endpoint
        """
        picking = selected_lines.mapped("picking_id")
        response = self.service.dispatch(
            "scan_line", params={"picking_id": picking.id, "barcode": barcode}
        )
        self._assert_selected(
            response,
            selected_lines,
            related_lines=related_lines,
            packing_info=packing_info,
        )
