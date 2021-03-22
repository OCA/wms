# Copyright 2020 Camptocamp SA (http://www.camptocamp.com)
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
from .test_checkout_base import CheckoutCommonCase
from .test_checkout_select_package_base import CheckoutSelectPackageMixin


class SelectDestPackageMixin:
    def _assert_response_select_dest_package(
        self, response, picking, selected_lines, packages, message=None
    ):
        picking_data = self.data.picking(picking)
        picking_data.update(
            {
                "note": None,
                "origin": None,
                "weight": 110.0,
                "move_line_count": len(picking.move_line_ids),
            }
        )
        self.assert_response(
            response,
            next_state="select_dest_package",
            data={
                "picking": picking_data,
                "packages": [
                    self._package_data(
                        package.with_context(picking_id=picking.id), picking
                    )
                    for package in packages
                ],
                "selected_move_lines": [
                    self._move_line_data(ml) for ml in selected_lines.sorted()
                ],
            },
            message=message,
        )


class CheckoutListDestPackageCase(
    CheckoutCommonCase, CheckoutSelectPackageMixin, SelectDestPackageMixin
):
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
        delivery_packaging = self.env.ref(
            "stock_storage_type.product_product_9_packaging_single_bag"
        )
        delivery_package = self.env["stock.quant.package"].create(
            {"packaging_id": delivery_packaging.id}
        )
        picking.move_lines[1].move_line_ids.result_package_id = delivery_package
        response = self.service.dispatch(
            "list_dest_package",
            params={
                "picking_id": picking.id,
                "selected_line_ids": picking.move_line_ids.ids,
            },
        )
        self._assert_response_select_dest_package(
            response, picking, picking.move_line_ids, delivery_package
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
            message={"message_type": "warning", "body": "No valid package to select."},
        )


class CheckoutScanSetDestPackageCase(CheckoutCommonCase, SelectDestPackageMixin):
    @classmethod
    def setUpClassBaseData(cls):
        super().setUpClassBaseData()
        picking = cls._create_picking(
            lines=[
                (cls.product_a, 10),
                (cls.product_b, 10),
                (cls.product_c, 10),
                (cls.product_d, 10),
            ]
        )
        pack1_moves = picking.move_lines[:3]
        pack2_moves = picking.move_lines[3:]
        # put in 2 packs, for this test, we'll work on pack1
        cls._fill_stock_for_moves(pack1_moves, in_package=True)
        cls._fill_stock_for_moves(pack2_moves, in_package=True)
        picking.action_assign()

        cls.selected_lines = pack1_moves.move_line_ids
        cls.pack1 = pack1_moves.move_line_ids.package_id
        cls.delivery_packaging = cls.env.ref(
            "stock_storage_type.product_product_9_packaging_single_bag"
        )
        cls.delivery_package = cls.env["stock.quant.package"].create(
            {"packaging_id": cls.delivery_packaging.id}
        )
        cls.move_line1, cls.move_line2, cls.move_line3 = cls.selected_lines
        # The 'scan_dest_package' and 'set_dest_package' methods can not be
        # used at all if there is no valid delivery package on the picking
        # (the user is redirected to the 'select_package' step in that case),
        # so we need at least to set one to pass this check in order to test
        # them
        cls.move_line1.result_package_id = cls.delivery_package
        # We'll put only product A and B in the destination package
        cls.move_line1.qty_done = cls.move_line1.product_uom_qty
        cls.move_line2.qty_done = cls.move_line2.product_uom_qty
        cls.move_line3.qty_done = 0

        cls.picking = picking

    def _get_allowed_packages(self, picking):
        return (
            picking.mapped("move_line_ids.package_id")
            | picking.mapped("move_line_ids.result_package_id")
        ).filtered("packaging_id")

    def _assert_package_set(self, response):
        self.assertRecordValues(
            self.move_line1 + self.move_line2 + self.move_line3,
            [
                {
                    "result_package_id": self.delivery_package.id,
                    "shopfloor_checkout_done": True,
                },
                {
                    "result_package_id": self.delivery_package.id,
                    "shopfloor_checkout_done": True,
                },
                # qty_done was zero so we don't set it as packed
                {"result_package_id": self.pack1.id, "shopfloor_checkout_done": False},
            ],
        )
        self.assert_response(
            response,
            # go pack to the screen to select lines to put in packages
            next_state="select_line",
            data={"picking": self._stock_picking_data(self.picking)},
            message=self.msg_store.goods_packed_in(self.delivery_package),
        )

    def test_scan_dest_package_ok(self):
        response = self.service.dispatch(
            "scan_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                # we keep the goods in the same package, so we scan the source package
                "barcode": self.delivery_package.name,
            },
        )
        self._assert_package_set(response)

    def test_scan_dest_package_error_not_found(self):
        barcode = "NO BARCODE"
        response = self.service.dispatch(
            "scan_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                "barcode": barcode,
            },
        )
        self._assert_response_select_dest_package(
            response,
            self.picking,
            self.selected_lines,
            self._get_allowed_packages(self.picking),
            message=self.service.msg_store.package_not_found_for_barcode(barcode),
        )

    def test_scan_dest_package_error_not_allowed(self):
        package = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "scan_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                "barcode": package.name,
            },
        )
        self._assert_response_select_dest_package(
            response,
            self.picking,
            self.selected_lines,
            self._get_allowed_packages(self.picking),
            message=self.service.msg_store.dest_package_not_valid(package),
        )

    def test_set_dest_package_ok(self):
        response = self.service.dispatch(
            "set_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                "package_id": self.delivery_package.id,
            },
        )
        self._assert_package_set(response)

    def test_set_dest_package_error_not_found(self):
        response = self.service.dispatch(
            "set_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                "package_id": 0,
            },
        )
        self._assert_response_select_dest_package(
            response,
            self.picking,
            self.selected_lines,
            self._get_allowed_packages(self.picking),
            message=self.service.msg_store.record_not_found(),
        )

    def test_set_dest_package_error_not_allowed(self):
        package = self.env["stock.quant.package"].create({})
        response = self.service.dispatch(
            "set_dest_package",
            params={
                "picking_id": self.picking.id,
                "selected_line_ids": self.selected_lines.ids,
                "package_id": package.id,
            },
        )
        self._assert_response_select_dest_package(
            response,
            self.picking,
            self.selected_lines,
            self._get_allowed_packages(self.picking),
            message=self.service.msg_store.dest_package_not_valid(package),
        )
