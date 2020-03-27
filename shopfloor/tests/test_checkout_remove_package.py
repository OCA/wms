from .test_checkout_base import CheckoutCommonCase


class CheckoutRemovePackageCase(CheckoutCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.picking = picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        cls.pack1_moves = picking.move_lines[:2]
        cls.pack2_moves = picking.move_lines[2]
        cls.raw_move = picking.move_lines[3]
        cls._fill_stock_for_moves(cls.pack1_moves, in_package=True)
        cls._fill_stock_for_moves(cls.pack2_moves, in_package=True)
        cls._fill_stock_for_moves(cls.raw_move)
        picking.action_assign()

    def test_remove_package_ok(self):
        picking = self.picking

        pack1_lines = self.pack1_moves.move_line_ids
        pack2_lines = self.pack2_moves.move_line_ids
        raw_line = self.raw_move.move_line_ids

        # do as we packed the lines in 2 different packages
        new_package = self.env["stock.quant.package"].create({})
        (pack1_lines | raw_line).write(
            {
                "qty_done": 10,
                "result_package_id": new_package.id,
                "shopfloor_checkout_packed": True,
            }
        )
        new_package2 = self.env["stock.quant.package"].create({})
        pack2_lines.write(
            {
                "qty_done": 10,
                "result_package_id": new_package2.id,
                "shopfloor_checkout_packed": True,
            }
        )

        # and now, we want to drop the new_package
        response = self.service.dispatch(
            "remove_package",
            params={"picking_id": picking.id, "package_id": new_package.id},
        )

        self.assertRecordValues(
            pack1_lines + raw_line + pack2_lines,
            [
                {
                    "qty_done": 0,
                    # reset to origin package
                    "result_package_id": pack1_lines.mapped("package_id").id,
                    "shopfloor_checkout_packed": False,
                },
                {
                    "qty_done": 0,
                    # reset to origin package
                    "result_package_id": pack1_lines.mapped("package_id").id,
                    "shopfloor_checkout_packed": False,
                },
                {
                    "qty_done": 0,
                    # result to an empty package (raw product)
                    "result_package_id": False,
                    "shopfloor_checkout_packed": False,
                },
                # different package, leave untouched
                {
                    "qty_done": 10,
                    "result_package_id": new_package2.id,
                    "shopfloor_checkout_packed": True,
                },
            ],
        )

        self.assert_response(
            response,
            next_state="summary",
            data={"picking": self._stock_picking_data(picking)},
        )

    def test_remove_package_error_package_not_found(self):
        # and now, we want to drop the new_package
        response = self.service.dispatch(
            "remove_package", params={"picking_id": self.picking.id, "package_id": 0}
        )
        self.assert_response(
            response,
            next_state="summary",
            data={"picking": self._stock_picking_data(self.picking)},
            message={
                "message_type": "error",
                "message": "The record you were working on does not exist anymore.",
            },
        )
