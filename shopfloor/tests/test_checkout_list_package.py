from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class CheckoutListDestPackageCase(CheckoutCommonCase, CheckoutSelectPackageMixin):
    def test_list_dest_package_ok(self):
        picking = self._create_picking(
            lines=[
                (self.product_a, 10),
                (self.product_b, 10),
                (self.product_c, 10),
                (self.product_d, 10),
            ]
        )
        self._fill_stock_for_moves(picking.move_lines[:2], in_package=True)
        self._fill_stock_for_moves(picking.move_lines[2], in_package=True)
        self._fill_stock_for_moves(picking.move_lines[3], in_package=True)
        picking.action_assign()
        new_package = self.env["stock.quant.package"].create({})
        picking.move_lines[1].move_line_ids.result_package_id = new_package

        packages = picking.mapped("move_line_ids.package_id") | new_package

        response = self.service.dispatch(
            "list_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
            },
        )
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": {
                    "id": picking.id,
                    "name": picking.name,
                    "note": "",
                    "origin": "",
                    "line_count": len(picking.move_line_ids),
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
                "packages": [
                    self._package_data(picking, package) for package in packages
                ],
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in picking.move_line_ids.sorted()
                ],
            },
        )

    def test_list_dest_package_error_no_package(self):
        picking = self._create_picking(
            lines=[
                (self.product_a, 10),
                (self.product_b, 10),
                (self.product_c, 10),
                (self.product_d, 10),
            ]
        )
        self._fill_stock_for_moves(picking.move_lines)
        picking.action_assign()
        self.assertEqual(picking.state, "assigned")
        response = self.service.dispatch(
            "list_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
            },
        )
        self._assert_selected_response(
            response,
            picking.move_line_ids,
            message={
                "message_type": "warning",
                "message": "No valid package to select.",
            },
        )
