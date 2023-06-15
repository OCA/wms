# Copyright 2023 Camptocamp SA
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl)

from odoo.addons.shopfloor_single_product_transfer.tests.common import CommonCase


class TestForcePackage(CommonCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.location = cls.location_src
        cls.product = cls.product_a

    @classmethod
    def _setup_picking(cls):
        cls._add_stock_to_product(cls.product, cls.location, 10)
        return cls._create_picking(lines=[(cls.product, 10)])

    def test_force_package_mandatory_no_package(self):
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.dispatch_location.sudo().package_restriction = "singlepackage"
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_done,
                "barcode": self.dispatch_location.barcode,
            },
        )
        data = {
            "move_line": self._data_for_move_line(move_line),
            "asking_confirmation": False,
        }
        expected_message = self.msg_store.location_requires_package()
        self.assert_response(
            response, next_state="set_quantity", data=data, message=expected_message
        )

    def test_force_package_mandatory_with_package(self):
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        package = self.env["stock.quant.package"].sudo().create({})
        move_line.result_package_id = package
        self.dispatch_location.sudo().package_restriction = "singlepackage"
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_done,
                "barcode": package.name,
            },
        )
        expected_data = {
            "move_line": self._data_for_move_line(move_line),
            "package": self._data_for_package(package),
        }
        self.assert_response(
            response,
            next_state="set_location",
            data=expected_data,
        )

    def test_force_package_not_mandatory(self):
        picking = self._setup_picking()
        move_line = picking.move_line_ids
        self.dispatch_location.sudo().package_restriction = "norestriction"
        response = self.service.dispatch(
            "set_quantity",
            params={
                "selected_line_id": move_line.id,
                "quantity": move_line.qty_done,
                "barcode": self.dispatch_location.barcode,
            },
        )
        data = {
            "location": self._data_for_location(self.location),
        }
        expected_message = self.msg_store.transfer_done_success(move_line.picking_id)
        self.assert_response(
            response, next_state="select_product", data=data, message=expected_message
        )
