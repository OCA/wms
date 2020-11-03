# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase


class CheckoutListSetPackagingCase(CheckoutCommonCase):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        pallet_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create({"name": "Pallet", "code": "P", "sequence": 3})
        )
        cls.packaging_pallet = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "packaging_type_id": pallet_type.id,
                    "name": "Pallet",
                    "barcode": "PPP",
                    "height": 100,
                    "width": 100,
                    "lngth": 100,
                }
            )
        )
        box_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create({"name": "Box", "code": "B", "sequence": 2})
        )
        cls.packaging_box = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "packaging_type_id": box_type.id,
                    "name": "Box",
                    "barcode": "BBB",
                    "height": 20,
                    "width": 20,
                    "lngth": 20,
                }
            )
        )
        inner_box_type = (
            cls.env["product.packaging.type"]
            .sudo()
            .create({"name": "Inner Box", "code": "I", "sequence": 1})
        )
        cls.packaging_inner_box = (
            cls.env["product.packaging"]
            .sudo()
            .create(
                {
                    "packaging_type_id": inner_box_type.id,
                    "name": "Inner Box",
                    "barcode": "III",
                    "height": 10,
                    "width": 10,
                    "lngth": 10,
                }
            )
        )
        cls.picking = cls._create_picking(lines=[(cls.product_a, 10)])
        cls._fill_stock_for_moves(cls.picking.move_lines, in_package=True)
        cls.picking.action_assign()
        cls.package = cls.picking.move_line_ids.result_package_id
        cls.package.packaging_id = cls.packaging_pallet

    def test_list_packaging_ok(self):
        response = self.service.dispatch(
            "list_packaging",
            params={"picking_id": self.picking.id, "package_id": self.package.id},
        )

        self.assert_response(
            response,
            next_state="change_packaging",
            data={
                "picking": self._picking_summary_data(self.picking),
                "package": self._package_data(self.package, self.picking),
                "packaging": [
                    self._packaging_data(packaging)
                    for packaging in self.packaging_inner_box
                    + self.packaging_box
                    + self.packaging_pallet
                ],
            },
        )

    def test_list_packaging_error_package_not_found(self):
        response = self.service.dispatch(
            "list_packaging", params={"picking_id": self.picking.id, "package_id": 0}
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": False,
            },
            message={
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
        )

    def test_set_packaging_ok(self):
        response = self.service.dispatch(
            "set_packaging",
            params={
                "picking_id": self.picking.id,
                "package_id": self.package.id,
                "packaging_id": self.packaging_inner_box.id,
            },
        )
        self.assertRecordValues(
            self.package, [{"packaging_id": self.packaging_inner_box.id}]
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": False,
            },
            message={
                "message_type": "success",
                "body": "Packaging changed on package {}".format(self.package.name),
            },
        )

    def test_set_packaging_error_package_not_found(self):
        response = self.service.dispatch(
            "set_packaging",
            params={
                "picking_id": self.picking.id,
                "package_id": 0,
                "packaging_id": self.packaging_inner_box.id,
            },
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": False,
            },
            message={
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
        )

    def test_set_packaging_error_packaging_not_found(self):
        response = self.service.dispatch(
            "set_packaging",
            params={
                "picking_id": self.picking.id,
                "package_id": self.package.id,
                "packaging_id": 0,
            },
        )
        self.assert_response(
            response,
            next_state="summary",
            data={
                "picking": self._stock_picking_data(self.picking, done=True),
                "all_processed": False,
            },
            message={
                "message_type": "error",
                "body": "The record you were working on does not exist anymore.",
            },
        )
