class CheckoutSelectPackageMixin:
    def _assert_selected_response(self, response, selected_lines, message=None):
        picking = selected_lines.mapped("picking_id")
        self.assert_response(
            response,
            next_state="select_package",
            data={
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in selected_lines
                ],
                "picking": {
                    "id": picking.id,
                    "name": picking.name,
                    "note": "",
                    "origin": "",
                    "line_count": len(picking.move_line_ids),
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
            },
            message=message,
        )

    def _assert_selected_qties(
        self, response, selected_lines, lines_quantities, message=None
    ):
        picking = selected_lines.mapped("picking_id")
        deselected_lines = picking.move_line_ids - selected_lines
        self.assertEqual(selected_lines.ids, [l.id for l in lines_quantities])
        for line, quantity in lines_quantities.items():
            self.assertEqual(line.qty_done, quantity)
        for line in deselected_lines:
            self.assertEqual(line.qty_done, 0, "Lines deselected must have no qty done")
        self._assert_selected_response(response, selected_lines, message=message)

    def _assert_selected(self, response, selected_lines, message=None):
        picking = selected_lines.mapped("picking_id")
        unselected_lines = picking.move_line_ids - selected_lines
        for line in selected_lines:
            self.assertEqual(
                line.qty_done,
                line.product_uom_qty,
                "Scanned lines must have their qty done set to the reserved quantity",
            )
        for line in unselected_lines:
            self.assertEqual(line.qty_done, 0)
        self._assert_selected_response(response, selected_lines, message=message)
