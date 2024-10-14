# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


class CheckoutSelectPackageMixin:
    def _assert_selected_response(
        self,
        response,
        selected_lines,
        message=None,
        packing_info="",
        no_package_enabled=True,
        package_allowed=True,
    ):
        picking = selected_lines.mapped("picking_id")
        self.assert_response(
            response,
            next_state="select_package",
            data={
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in selected_lines.sorted()
                ],
                "picking": self._picking_summary_data(picking),
                "no_package_enabled": no_package_enabled,
                "package_allowed": package_allowed,
            },
            message=message,
        )

    def _assert_selected_qties(
        self,
        response,
        selected_lines,
        lines_quantities,
        message=None,
        packing_info="",
    ):
        picking = selected_lines.mapped("picking_id")
        deselected_lines = picking.move_line_ids - selected_lines
        self.assertEqual(
            sorted(selected_lines.ids), sorted([line.id for line in lines_quantities])
        )
        for line, quantity in lines_quantities.items():
            self.assertEqual(line.qty_done, quantity)
        for line in deselected_lines:
            self.assertEqual(line.qty_done, 0, "Lines deselected must have no qty done")
        self._assert_selected_response(
            response, selected_lines, message=message, packing_info=packing_info
        )

    def _assert_selected(
        self, response, selected_lines, related_lines=None, message=None, **kw
    ):
        related_lines = related_lines or self.env["stock.move.line"]
        picking = selected_lines.mapped("picking_id")
        unselected_lines = picking.move_line_ids - selected_lines
        for line in selected_lines - related_lines:
            self.assertEqual(
                line.qty_done,
                line.product_uom_qty,
                "Scanned lines must have their qty done set to the reserved quantity",
            )
        for line in unselected_lines + related_lines:
            self.assertEqual(line.qty_done, 0)
        package_lines = selected_lines + related_lines
        self._assert_selected_response(response, package_lines, message=message, **kw)
