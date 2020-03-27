from .test_checkout_base import CheckoutCommonCase


class CheckoutListPackagingCase(CheckoutCommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.packaging_pallet = cls.env["product.packaging"].create(
            {
                "sequence": 3,
                "name": "Pallet",
                "barcode": "PPP",
                "height": 100,
                "width": 100,
                "lngth": 100,
            }
        )
        cls.packaging_box = cls.env["product.packaging"].create(
            {
                "sequence": 2,
                "name": "Box",
                "barcode": "BBB",
                "height": 20,
                "width": 20,
                "lngth": 20,
            }
        )
        cls.packaging_inner_box = cls.env["product.packaging"].create(
            {
                "sequence": 1,
                "name": "Inner Box",
                "barcode": "III",
                "height": 10,
                "width": 10,
                "lngth": 10,
            }
        )

    def test_list_packaging_ok(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        self._fill_stock_for_moves(picking.move_lines, in_package=True)
        picking.action_assign()
        package = picking.move_line_ids.result_package_id
        response = self.service.dispatch(
            "list_packaging",
            params={"picking_id": picking.id, "package_id": package.id},
        )

        self.assert_response(
            response,
            next_state="change_packaging",
            data={
                "picking": {
                    "id": picking.id,
                    "name": picking.name,
                    "note": "",
                    "origin": "",
                    "line_count": len(picking.move_line_ids),
                    "partner": {"id": self.customer.id, "name": self.customer.name},
                },
                "package": {
                    "id": package.id,
                    "name": package.name,
                    # TODO
                    "weight": 0,
                    "line_count": 1,
                    "packaging_name": package.product_packaging_id.name or "",
                },
                "packagings": [
                    {
                        "id": self.packaging_inner_box.id,
                        "name": self.packaging_inner_box.name,
                    },
                    {"id": self.packaging_box.id, "name": self.packaging_box.name},
                    {
                        "id": self.packaging_pallet.id,
                        "name": self.packaging_pallet.name,
                    },
                ],
            },
        )

    def test_list_packaging_error_package_not_found(self):
        picking = self._create_picking(lines=[(self.product_a, 10)])
        response = self.service.dispatch(
            "list_packaging", params={"picking_id": picking.id, "package_id": 0}
        )
        self.assert_response(
            response,
            next_state="summary",
            data={"picking": self._stock_picking_data(picking)},
            message={
                "message_type": "error",
                "message": "The record you were working on does not exist anymore.",
            },
        )
